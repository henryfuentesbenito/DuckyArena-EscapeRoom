import { apiGet, apiPost } from "../api.js";
import { openPuzzleModal } from "../ui/puzzle-modal.js";
import { SFX } from "../sfx.js";

const ERA_COLORS = {
  1: { top: 0x3a2f20, bottom: 0x1a1308 },
  2: { top: 0x1e3a5f, bottom: 0x0a1c33 },
  3: { top: 0x5f1e1e, bottom: 0x330a0a },
  4: { top: 0x2a2a3a, bottom: 0x14141f },
  5: { top: 0x3f2c5f, bottom: 0x1f1430 },
  6: { top: 0x2b2420, bottom: 0x140e0a },
  7: { top: 0x1a2b3f, bottom: 0x0a1420 },
};
const THEME_OBJECTS = {
  PRISON: { emoji: "🔑", bg: 0x8b4a4a, label: "la llave" },
  SCHOOL: { emoji: "📜", bg: 0x4a6b3a, label: "el pergamino" },
  LAB: { emoji: "⚗️", bg: 0x3a5478, label: "el matraz" },
};

export default class RoomScene extends Phaser.Scene {
  constructor() {
    super("RoomScene");
  }

  init(data) {
    this.sessionId = data.sessionId;
    this.escapeRoom = data.escapeRoom;
    this.resumed = !!data.resumed;
    this.oldCoins = data.oldCoins;
    this.state = null;
    this.modalApi = null;
    this.expireChecked = false;
  }

  async create() {
    const W = this.scale.width;
    const H = this.scale.height;

    // Fondo con color por era
    const era = (this.escapeRoom && this.escapeRoom.era) || 1;
    const c = ERA_COLORS[era] || ERA_COLORS[1];
    const bg = this.add.graphics();
    bg.fillGradientStyle(c.top, c.top, c.bottom, c.bottom, 1);
    bg.fillRect(0, 0, W, H);
    // Fondos por sala: se elige la imagen después de recibir el estado oficial Django.
    this.roomBackground = this.add.image(W / 2, H / 2, "escape-cueva")
      .setDisplaySize(W, H).setAlpha(0).setDepth(0);
    this.add.rectangle(W / 2, 31, W, 62, 0x061422, 0.83).setDepth(2);
    this.add.rectangle(W / 2, H - 65, W, 130, 0x061422, 0.88).setDepth(2);
    for (let i = 0; i < 40; i++) {
      const x = Phaser.Math.Between(0, W);
      const y = Phaser.Math.Between(0, H * 0.5);
      this.add.circle(
        x,
        y,
        Phaser.Math.FloatBetween(0.5, 1.5),
        0xffffff,
        Phaser.Math.FloatBetween(0.2, 0.6),
      );
    }

    this.loadingText = this.add
      .text(W / 2, H / 2, "Cargando partida...", {
        fontFamily: "monospace",
        fontSize: "22px",
        color: "#fff",
      })
      .setOrigin(0.5);

    this.add.text(W - 16, 14, "← Arena", {fontFamily:"monospace",fontSize:"18px",color:"#ffd54f",backgroundColor:"#081826",padding:{x:12,y:8}})
      .setOrigin(1,0).setDepth(200).setInteractive({useHandCursor:true})
      .on("pointerdown",()=>{if(window.confirm("¿Salir a Arena? La partida seguirá contando tiempo mientras esté activa.")) window.location.assign("/arena/");});
    this.add.text(W - 16, 57, "Temáticas", {fontFamily:"monospace",fontSize:"17px",color:"#8ae5dd",backgroundColor:"#081826",padding:{x:12,y:8}})
      .setOrigin(1,0).setDepth(200).setInteractive({useHandCursor:true})
      .on("pointerdown",()=>{if(window.confirm("¿Volver a temáticas? La partida seguirá contando tiempo mientras esté activa.")) window.location.assign("/escape/game/");});
    // ESC → hub
    this.input.keyboard.on("keydown-ESC", () => {
      this.closeModal();
      this.scene.start("HubScene");
    });

    // Al volver a la pestaña después de un rato, refrescar estado
    this._visibilityHandler = () => {
      if (
        document.visibilityState === "visible" &&
        this.state &&
        !this.state.finished
      ) {
        this.silentRefresh();
      }
    };
    document.addEventListener("visibilitychange", this._visibilityHandler);
    this.events.once("shutdown", () => {
      document.removeEventListener("visibilitychange", this._visibilityHandler);
      this.closeModal();
    });

    try {
      await this.loadState();
      this.loadingText.destroy();
      if (this.state.finished) {
        if (this.state.session.status === "COMPLETED") this.showVictory();
        else this.showDefeat();
        return;
      }
      this.renderRoomArt();
      this.renderHUD();
      this.renderStageInfo();
      this.renderWorld();
      if (this.resumed) {
        this.showToast("📋 Partida reanudada", "#64b5f6");
      }
      // Monedas recién ganadas al cerrar una habitación
      if (typeof this.oldCoins === "number") {
        const diff = (this.state.session.coins || 0) - this.oldCoins;
        if (diff > 0) {
          this.showToast(
            `🪙 +${diff} monedas por completar la habitación`,
            "#ffd54f",
          );
        }
      }
    } catch (err) {
      this.loadingText.setText("Error: " + err.message);
      this.loadingText.setColor("#ff6b6b");
      console.error(err);
    }
    this.add
      .text(
        10,
        this.scale.height - 10,
        "Explora · WASD / flechas / clic · Los desafíos se validan en Django",
        {
          fontFamily: "monospace",
          fontSize: "11px",
          color: "#555",
        },
      )
      .setOrigin(0, 1);
  }

  renderRoomArt() {
    const key = ({1: "escape-cueva", 2: "escape-taller", 3: "escape-portal"})[this.state.room.order] || "escape-cueva";
    if (this.textures.exists(key)) this.roomBackground.setTexture(key).setAlpha(1);
  }

  async loadState() {
    this.state = await apiGet(`/escape/api/session/${this.sessionId}/state/`);
    if (!this.state.ok)
      throw new Error(this.state.error || "Error del backend");
  }

  async silentRefresh() {
    // Refresca state sin repintar la escena (solo para detectar expiración).
    try {
      const old = this.state;
      await this.loadState();
      if (this.state.finished && !old.finished) {
        this.closeModal();
        this.scene.restart({
          sessionId: this.sessionId,
          escapeRoom: this.escapeRoom,
        });
      } else if (!this.state.finished) {
        // Sincroniza el reloj por si el backend dice menos tiempo
        this.state.session.remaining_seconds =
          this.state.session.remaining_seconds;
      }
    } catch (err) {
      console.warn("silentRefresh:", err);
    }
  }

  renderHUD() {
    const W = this.scale.width;
    const s = this.state;

    this.add.rectangle(W / 2, 30, W, 60, 0x000000, 0.75);

    this.add.text(20, 20, s.session.escape_room.name, {
      fontFamily: "monospace",
      fontSize: "18px",
      color: "#ffd54f",
    });
    this.add.text(
      20,
      42,
      `Era ${s.session.escape_room.era} · ${s.session.escape_room.era_display}`,
      {
        fontFamily: "monospace",
        fontSize: "13px",
        color: "#bbb",
      },
    );

    this.add
      .text(
        W / 2,
        30,
        `Fase ${s.progress.completed_stages + 1} / ${s.progress.total_stages}`,
        {
          fontFamily: "monospace",
          fontSize: "18px",
          color: "#fff",
        },
      )
      .setOrigin(0.5);

    const mm = Math.floor(s.session.remaining_seconds / 60);
    const ss = s.session.remaining_seconds % 60;
    this.timerText = this.add
      .text(W - 20, 20, `⏱ ${mm}:${ss.toString().padStart(2, "0")}`, {
        fontFamily: "monospace",
        fontSize: "18px",
        color: "#ffd54f",
      })
      .setOrigin(1, 0);
    this.add
      .text(
        W - 20,
        42,
        `Puntuación local: ${s.session.score}`,
        {
          fontFamily: "monospace",
          fontSize: "13px",
          color: "#ffd54f",
        },
      )
      .setOrigin(1, 0);

    // Botón "Abandonar" en la esquina superior derecha, destacado, con depth alto
    this.abandonBtn = this.add
      .text(W - 20, 72, " ✕ Abandonar ", {
        fontFamily: "monospace",
        fontSize: "14px",
        color: "#fff",
        backgroundColor: "#8b2a2a",
        padding: { x: 10, y: 6 },
      })
      .setOrigin(1, 0)
      .setInteractive({ useHandCursor: true })
      .setDepth(100);

    this.abandonBtn.on("pointerover", () =>
      this.abandonBtn.setBackgroundColor("#c53535"),
    );
    this.abandonBtn.on("pointerout", () =>
      this.abandonBtn.setBackgroundColor("#8b2a2a"),
    );
    this.abandonBtn.on("pointerdown", (pointer, localX, localY, event) => {
      // Importante: evitar que el click llegue al pergamino u otros objetos
      if (event && event.stopPropagation) event.stopPropagation();
      this.confirmAbandon();
    });

    this.pauseBtn = this.add.text(W - 20, 116, s.session.status === "PAUSED" ? "▶ Continuar" : "Ⅱ Pausar", {fontFamily:"monospace",fontSize:"14px",color:"#fff",backgroundColor:"#12666a",padding:{x:10,y:7}}).setOrigin(1,0).setInteractive({useHandCursor:true}).setDepth(110);
    this.pauseBtn.on("pointerdown", async () => {
      try {
        const endpoint = this.state.session.status === "PAUSED" ? "resume" : "pause";
        const result = await apiPost(`/escape/api/session/${this.sessionId}/${endpoint}/`, {});
        if (!result.ok) throw new Error(result.error || "No se pudo cambiar la pausa");
        this.scene.restart({sessionId:this.sessionId,escapeRoom:this.escapeRoom});
      } catch(e) {this.showToast(e.message)}
    });
    // Timer que decrementa cada segundo + auto-chequeo al expirar
    this.timerEvent = this.time.addEvent({
      delay: 1000,
      loop: true,
      callback: () => this._tickTimer(),
    });
  }

  async _tickTimer() {
    if (!this.state || this.state.finished) return;
    if (this.state.session.status === "PAUSED") return;
    this.state.session.remaining_seconds = Math.max(0, this.state.session.remaining_seconds - 1);
    const sec = this.state.session.remaining_seconds;
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    this.timerText.setText(`⏱ ${m}:${s.toString().padStart(2, "0")}`);
    // Color según urgencia
    if (sec <= 30) this.timerText.setColor("#ff6b6b");
    else if (sec <= 60) this.timerText.setColor("#ff9800");
    else this.timerText.setColor("#ffd54f");

    // Al expirar, pregunta al backend una vez
    if (sec === 0 && !this.expireChecked) {
      this.expireChecked = true;
      await this.silentRefresh();
    }
  }

  renderStageInfo() {
    const W = this.scale.width;
    const s = this.state;
    // El escenario es el protagonista. No se dibuja un segundo panel gigante
    // sobre la ilustración ni un objeto genérico que oculte el Ducky.
    this.add.text(20, 78, `SALA · ${s.room.name}`, {
      fontFamily: "monospace", fontSize: "20px", color: "#fff",
      stroke: "#061422", strokeThickness: 5,
    }).setDepth(40);
    this.add.text(20, 109, `OBJETIVO · ${s.stage.name}`, {
      fontFamily: "monospace", fontSize: "17px", color: "#ffda78",
      stroke: "#061422", strokeThickness: 5,
    }).setDepth(40);
    this.add.text(W / 2, this.scale.height - 147,
      "Explora los puntos brillantes · Usa el inventario · Resuelve el desafío", {
        fontFamily: "monospace", fontSize: "13px", color: "#e8f8ff",
        backgroundColor: "#071a29", padding: {x:12,y:8},
      }).setOrigin(0.5).setDepth(65);
    this.add.text(W - 20, this.scale.height - 147, "◈ DESAFÍO", {
      fontFamily: "monospace", fontSize: "15px", color: "#ffd54f",
      backgroundColor: "#092030", padding: {x:12,y:9},
    }).setOrigin(1,0.5).setInteractive({useHandCursor:true}).setDepth(75)
      .on("pointerdown",()=>this.openPuzzle());
  }
  renderWorld() {
    const W=this.scale.width, H=this.scale.height;
    const world=this.state.world || {inventory:[],interactables:[]};
    this.selectedItem=null;
    this.add.rectangle(W/2,H-72,W,90,0x071a29,.95).setDepth(60);
    this.add.text(15,H-112,"INVENTARIO · selecciona un objeto para usarlo",{fontFamily:"monospace",fontSize:"13px",color:"#efc86a"}).setDepth(61);
    world.inventory.forEach((item,i)=>{
      const label=this.add.text(18+i*185,H-83,`${item.name} ×${item.quantity}`,{fontFamily:"monospace",fontSize:"12px",color:"#fff",backgroundColor:"#24526a",padding:{x:7,y:9}}).setInteractive({useHandCursor:true}).setDepth(62);
      label.on("pointerdown",()=>{this.selectedItem=item.key;this.showToast(`Seleccionado: ${item.name}`,"#64e6db")});
    });
    world.interactables.filter(o=>o.state!=="collected").forEach((o,i)=>{
      const x=Math.round(o.x*W),y=Math.round(o.y*(H-230))+95;
      const color=o.state==="idle"?"#eac778":"#65dfb6";
      const label=this.add.text(x,y,`✦ ${o.label}${o.state !== "idle" ? " ✓" : ""}`,{fontFamily:"monospace",fontSize:"12px",color,backgroundColor:"#092030",padding:{x:8,y:6},align:"center"}).setOrigin(.5).setInteractive({useHandCursor:true}).setDepth(75);
      label.on("pointerdown",async()=>{
        const action=(this.selectedItem && o.actions.includes("use"))?"use":o.actions.includes("collect")?"collect":o.actions.includes("use")?"use":"inspect";
        try {
          const result=await apiPost(`/escape/api/session/${this.sessionId}/interact/`,{target_key:o.key,action,item_key:this.selectedItem});
          if(!result.ok)throw new Error(result.error||"Acción no disponible");
          this.scene.restart({sessionId:this.sessionId,escapeRoom:this.escapeRoom});
        } catch(e){this.showToast(e.message)}
      });
    });
    // MiniDucky existente, cuatro orientaciones y desplazamiento local visual.
    // El movimiento no modifica la partida ni concede resultados: Django sigue siendo autoritativo.
    this.miniDucky = this.add.image(W * 0.42, H - 160, "duck-down")
      .setDisplaySize(68, 75).setOrigin(.5, 1).setDepth(52);
    this.duckyFacing = "down";
    this.miniKeys = this.input.keyboard.addKeys("W,A,S,D,UP,DOWN,LEFT,RIGHT");
    this.input.on("pointerdown", pointer => {
      if (!this.miniDucky || this.modalApi || this.state.session.status !== "PLAYING") return;
      if (pointer.y < 155 || pointer.y > H - 130) return;
      this.duckyTarget = {x: Phaser.Math.Clamp(pointer.x, 90, W-90), y: Phaser.Math.Clamp(pointer.y, 245, H-145)};
    });
    this.events.on("update", (_, delta) => {
      if (!this.miniDucky || !this.miniDucky.active || this.modalApi || this.state.session.status !== "PLAYING") return;
      let dx = 0, dy = 0;
      const k=this.miniKeys;
      if(k.A.isDown||k.LEFT.isDown) dx--;
      if(k.D.isDown||k.RIGHT.isDown) dx++;
      if(k.W.isDown||k.UP.isDown) dy--;
      if(k.S.isDown||k.DOWN.isDown) dy++;
      if(dx||dy) this.duckyTarget=null;
      else if(this.duckyTarget){
        dx=this.duckyTarget.x-this.miniDucky.x;
        dy=this.duckyTarget.y-this.miniDucky.y;
        if(Math.hypot(dx,dy)<8){this.duckyTarget=null;return;}
      }
      const length=Math.hypot(dx,dy);
      if(length){
        const step=Math.min(185*delta/1000,length);
        this.miniDucky.x=Phaser.Math.Clamp(this.miniDucky.x+dx/length*step,85,W-85);
        this.miniDucky.y=Phaser.Math.Clamp(this.miniDucky.y+dy/length*step,255,H-145);
        const facing=Math.abs(dx)>Math.abs(dy)?(dx>0?"right":"left"):(dy>0?"down":"up");
        if(facing!==this.duckyFacing){this.duckyFacing=facing;this.miniDucky.setTexture(`duck-${facing}`)}
      }
    });
    this.add.text(16,H-150,`DUK-01: ${this.state.dialogue?.text||"Explora la sala"}`,{fontFamily:"monospace",fontSize:"12px",color:"#8bdfeb",wordWrap:{width:W-180}}).setDepth(65);
    if(this.state.session.status==="PAUSED")this.add.text(W/2,H/2,"PARTIDA EN PAUSA\nPulsa Continuar para jugar",{fontFamily:"monospace",fontSize:"25px",color:"#fff",backgroundColor:"#0b2436",padding:{x:25,y:20},align:"center"}).setOrigin(.5).setDepth(120);
  }

  // ─── Modal del puzzle ─────────────────────────────────────────

  openPuzzle() {
    if (this.modalApi) return;
    if (this.state.finished || this.state.session.status !== "PLAYING") return;
    SFX.open();
    this.input.keyboard.enabled = false;

    this.modalApi = openPuzzleModal(this.state, {
      onSubmit: (answer, api) => this.submitAnswer(answer, api),
      onHintRequest: (api) => this.requestHint(api),
      onCancel: () => this.closeModal(),
    });
  }

  closeModal() {
    if (this.modalApi && typeof this.modalApi.close === "function") {
      this.modalApi.close();
    } else {
      // Fallback defensivo: elimina el overlay si quedara huérfano en el DOM
      const el = document.getElementById("puzzle-modal");
      if (el) el.remove();
    }
    this.modalApi = null;
    this.input.keyboard.enabled = true;
  }

  async submitAnswer(answer, api) {
    api.disable();
    try {
      const res = await apiPost(
        `/escape/api/session/${this.sessionId}/submit/`,
        {
          puzzle_id: this.state.puzzle.id,
          answer: answer,
        },
      );

      if (!res.ok) {
        api.showFeedback("⚠ " + (res.error || "Error desconocido"), "#ff9800");
        api.enable();
        // Si el error es de sesión no activa, cerrar y refrescar
        if (res.status && res.status !== "PLAYING") {
          this.time.delayedCall(1800, () => {
            this.closeModal();
            this.scene.restart({
              sessionId: this.sessionId,
              escapeRoom: this.escapeRoom,
            });
          });
        }
        return;
      }

      if (res.is_correct) {
        SFX.correct();
        api.showFeedback("✓ ¡Correcto!", "#4caf50");
        const oldCoins = this.state.session.coins || 0;
        this.time.delayedCall(1200, () => {
          this.closeModal();
          this.scene.restart({
            sessionId: this.sessionId,
            escapeRoom: this.escapeRoom,
            oldCoins: oldCoins,
          });
        });
      } else {
        SFX.wrong();
        api.shake();
        api.showFeedback("✗ Incorrecto. Intenta de nuevo.", "#ff6b6b");
        if (res.failed) {
          this.time.delayedCall(1500, () => {
            this.closeModal();
            this.scene.restart({
              sessionId: this.sessionId,
              escapeRoom: this.escapeRoom,
            });
          });
        } else {
          api.enable();
        }
      }
    } catch (err) {
      console.error(err);
      api.showFeedback("Error de red: " + err.message, "#ff6b6b");
      api.enable();
    }
  }

  async requestHint(api) {
    try {
      const res = await apiPost(
        `/escape/api/session/${this.sessionId}/hint/`,
        {},
      );
      if (!res.ok) {
        api.showFeedback(
          "⚠ " + (res.error || "No hay pista disponible"),
          "#ff9800",
        );
        return;
      }
      SFX.hint();
      const h = res.hint;
      api.appendHintText(
        `${h.text} (−${h.penalty_seconds}s · −${h.penalty_points} pts)`,
      );
      // Refresca estado para saber si queda alguna pista más y
      // reactivar el botón del modal si corresponde.
      await this.loadState();
      api.setHint(this.state.hint);
    } catch (err) {
      console.error(err);
      api.showFeedback("Error de red: " + err.message, "#ff6b6b");
    }
  }

  // ─── Abandono ────────────────────────────────────────────────

  confirmAbandon() {
    if (this.modalApi) return;

    // Confirmación nativa del navegador — robusta, no choca con nada
    const ok = window.confirm(
      "¿Abandonar la aventura?\n\n" +
        "Perderás el progreso de esta partida. " +
        "Quedará marcada como ABANDONADA.",
    );
    if (!ok) return;

    this.doAbandon();
  }

  async doAbandon() {
    try {
      const res = await apiPost(
        `/escape/api/session/${this.sessionId}/abandon/`,
        {},
      );
      if (!res.ok) throw new Error(res.error || "No se pudo abandonar");
      this.closeModal();
      this.scene.restart({
        sessionId: this.sessionId,
        escapeRoom: this.escapeRoom,
      });
    } catch (err) {
      console.error(err);
      this.showToast("Error al abandonar: " + err.message, "#ff6b6b");
    }
  }

  // ─── Toast ────────────────────────────────────────────────────

  showToast(text, color = "#ff6b6b") {
    const W = this.scale.width;
    const H = this.scale.height;
    const bg = this.add
      .rectangle(W / 2, H - 100, 600, 50, 0x000000, 0.92)
      .setStrokeStyle(2, color);
    const txt = this.add
      .text(W / 2, H - 100, text, {
        fontFamily: "monospace",
        fontSize: "15px",
        color: color,
      })
      .setOrigin(0.5);
    this.tweens.add({
      targets: [bg, txt],
      alpha: { from: 1, to: 0 },
      delay: 2500,
      duration: 600,
      onComplete: () => {
        bg.destroy();
        txt.destroy();
      },
    });
  }

  // ─── Pantallas finales ────────────────────────────────────────

  showVictory() {
    SFX.victory();
    const W = this.scale.width;
    const H = this.scale.height;

    this.add.rectangle(W / 2, H / 2, W, H, 0x000000, 0.92);
    this.add
      .text(W / 2, 160, "¡HAS ESCAPADO!", {
        fontFamily: "monospace",
        fontSize: "68px",
        color: "#4caf50",
        stroke: "#000",
        strokeThickness: 6,
      })
      .setOrigin(0.5);
    this.add
      .text(W / 2, 240, this.state.session.escape_room.name, {
        fontFamily: "monospace",
        fontSize: "22px",
        color: "#fff",
      })
      .setOrigin(0.5);

    const s = this.state.settlement;
    if (s) {
      this.add
        .text(W / 2, 330, `Puntos base: ${s.gross_xp}`, {
          fontFamily: "monospace",
          fontSize: "20px",
          color: "#fff",
        })
        .setOrigin(0.5);
      this.add
        .text(W / 2, 365, `Penalización: −${s.penalty_xp}`, {
          fontFamily: "monospace",
          fontSize: "20px",
          color: "#ff9800",
        })
        .setOrigin(0.5);
      this.add
        .text(W / 2, 400, `Bonus: +${s.bonus_xp}`, {
          fontFamily: "monospace",
          fontSize: "20px",
          color: "#64b5f6",
        })
        .setOrigin(0.5);
      this.add
        .text(W / 2, 480, `PUNTUACIÓN TOTAL: ${s.final_xp}`, {
          fontFamily: "monospace",
          fontSize: "36px",
          color: "#ffd54f",
          stroke: "#000",
          strokeThickness: 4,
        })
        .setOrigin(0.5);
    }
    const coins = this.state.session.coins || 0;
    this.add
      .text(W / 2, 525, `Puntuación exclusiva de Escape`, {
        fontFamily: "monospace",
        fontSize: "24px",
        color: "#ffd54f",
        stroke: "#000",
        strokeThickness: 3,
      })
      .setOrigin(0.5);

    const st = this.state.stats || {};
    this.add
      .text(
        W / 2,
        560,
        `Intentos: ${st.attempts || 0}  ·  Fallos: ${st.fails || 0}  ·  Pistas: ${st.hints_used || 0}`,
        {
          fontFamily: "monospace",
          fontSize: "16px",
          color: "#aaa",
        },
      )
      .setOrigin(0.5);

    this.add
      .text(W / 2, H - 50, "Pulsa ESC para volver al hub", {
        fontFamily: "monospace",
        fontSize: "15px",
        color: "#888",
      })
      .setOrigin(0.5);
  }

  showDefeat() {
    SFX.defeat();
    const W = this.scale.width;
    const H = this.scale.height;

    this.add.rectangle(W / 2, H / 2, W, H, 0x000000, 0.92);
    this.add
      .text(W / 2, 220, "AVENTURA TERMINADA", {
        fontFamily: "monospace",
        fontSize: "52px",
        color: "#ff6b6b",
        stroke: "#000",
        strokeThickness: 5,
      })
      .setOrigin(0.5);

    const reasonText = {
      TIME_EXPIRED: "Se agotó el tiempo.",
      FAILED: "Demasiados intentos fallidos.",
      ABANDONED: "Has abandonado la aventura.",
      COMPLETED: "Aventura completada.",
    };
    const reason =
      (this.state.settlement && this.state.settlement.reason) ||
      this.state.session.status;
    this.add
      .text(W / 2, 300, reasonText[reason] || "La partida ha terminado.", {
        fontFamily: "monospace",
        fontSize: "20px",
        color: "#ddd",
      })
      .setOrigin(0.5);

    const coins = this.state.session.coins || 0;
    if (coins > 0) {
      this.add
        .text(W / 2, 365, `Puntuación exclusiva de Escape ganadas antes del fin`, {
          fontFamily: "monospace",
          fontSize: "20px",
          color: "#ffd54f",
        })
        .setOrigin(0.5);
    }

    const st = this.state.stats || {};
    this.add
      .text(
        W / 2,
        400,
        `Intentos: ${st.attempts || 0}  ·  Fallos: ${st.fails || 0}  ·  Pistas: ${st.hints_used || 0}`,
        {
          fontFamily: "monospace",
          fontSize: "18px",
          color: "#aaa",
        },
      )
      .setOrigin(0.5);

    this.add
      .text(W / 2, H - 50, "Pulsa ESC para volver al hub", {
        fontFamily: "monospace",
        fontSize: "15px",
        color: "#888",
      })
      .setOrigin(0.5);
  }
}

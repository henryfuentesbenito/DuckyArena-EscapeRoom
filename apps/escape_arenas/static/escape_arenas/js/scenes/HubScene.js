import { Music } from "../sfx.js";
export default class HubScene extends Phaser.Scene {
  constructor() {
    super("HubScene");
  }

  create() {
    const W = this.scale.width;
    const H = this.scale.height;

    // Escenario temático: fondo ilustrado, no una captura con botones incrustados.
    const bg = this.add.image(W / 2, H / 2, "escape-cueva");
    const fit = Math.max(W / bg.width, H / bg.height);
    bg.setScale(fit).setAlpha(0.64);
    this.add.rectangle(W / 2, H / 2, W, H, 0x081326, 0.40);
    const sky = this.add.graphics();
    sky.fillGradientStyle(0x071326, 0x071326, 0x071326, 0x071326, 0.7, 0.4, 0.12, 0.3);
    sky.fillRect(0, 0, W, H);
    this.add.text(W / 2, 32, "✦  DuckyArena  ✦", {
      fontFamily: "Georgia, serif", fontSize: "25px", color: "#ffda81",
      stroke: "#20100a", strokeThickness: 5,
    }).setOrigin(0.5);
    this.add.text(W / 2, 83, "ESCAPE ARENAS", {
      fontFamily: "Georgia, serif", fontStyle: "bold", fontSize: "62px", color: "#ffb53b",
      stroke: "#27110a", strokeThickness: 9,
    }).setOrigin(0.5);
    this.add.text(W / 2, 130, "El Laboratorio del Tiempo", {
      fontFamily: "Georgia, serif", fontSize: "23px", color: "#ffe7b5",
      backgroundColor: "#3b2418", padding: {x: 20, y: 7},
    }).setOrigin(0.5);
    this.add.text(W / 2, 174, "Elige una aventura para comenzar", {
      fontFamily: "Arial", fontSize: "19px", color: "#fff1cf", stroke: "#141414", strokeThickness: 4,
    }).setOrigin(0.5);
    this.add.text(22, 22, "← Volver a Arena", {
      fontFamily: "Arial", fontSize: "18px", color: "#ffe5a5", backgroundColor: "#172337",
      padding: {x: 15, y: 11},
    }).setInteractive({useHandCursor:true}).on("pointerdown",()=>window.location.assign("/arena/"));

    // ===== Pato =====
    this.player = this.createDuck(W / 2, H - 72);

    // ===== Hint text =====
    this.hint = this.add
      .text(W / 2, H - 15, "", {
        fontFamily: "monospace",
        fontSize: "20px",
        color: "#ffd54f",
        stroke: "#000",
        strokeThickness: 3,
      })
      .setOrigin(0.5);

    this.cursors = this.input.keyboard.createCursorKeys();
    this.enterKey = this.input.keyboard.addKey(
      Phaser.Input.Keyboard.KeyCodes.ENTER,
    );
    this.portals = [];
    this.overlayOpen = false;

    this.loadingText = this.add
      .text(W / 2, 360, "Cargando temáticas...", {
        fontFamily: "monospace",
        fontSize: "22px",
        color: "#fff",
      })
      .setOrigin(0.5);

    this.loadHub();
    Music.start();

  }

  createDuck(x, y) {
    const duck = this.physics.add.sprite(x, y, "duck-down");
    duck.setCollideWorldBounds(true);
    // Si tu sprite es muy pequeño/grande, ajusta estos dos valores.
    // Mantén un ratio cuadrado o respeta el aspecto original del sprite.
    duck.setDisplaySize(64, 64);
    // Hitbox más pequeño que el sprite para que colisione más natural.
    duck.body.setSize(40, 40);
    duck.body.setOffset((duck.width - 40) / 2, (duck.height - 40) / 2);
    duck.currentDir = "down";
    return duck;
  }

  async loadHub() {
    try {
      const res = await fetch("/escape/api/hub/", {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.loadingText.destroy();
      this.renderPortals(data.themes);
      // Se conserva exclusivamente el Ducky animado original del menú.
    } catch (err) {
      this.loadingText.setText("Error cargando el hub: " + err.message);
      console.error(err);
    }
  }

  renderPortals(themes) {
    const ordered = ["PRISON", "SCHOOL", "LAB"]
      .map(key => themes.find(t => t.key === key)).filter(Boolean);
    const labels = {
      PRISON: "Cárcel Temporal", SCHOOL: "Colegio del Tiempo", LAB: "Laboratorio Prehistórico"
    };
    const images = {PRISON: "escape-portal", SCHOOL: "escape-taller", LAB: "escape-cueva"};
    const positions = this.spreadX(ordered.length, 265);
    ordered.forEach((theme, i) => {
      const x = positions[i], y = 365;
      const available = theme.rooms.length > 0;
      const border = available ? 0xffbd48 : 0x69717b;
      const card = this.add.container(x, y);
      const shadow = this.add.rectangle(5, 6, 250, 306, 0x000000, .55);
      const panel = this.add.rectangle(0, 0, 250, 306, 0x1b2431, .98)
        .setStrokeStyle(available ? 5 : 3, border);
      const art = this.add.image(0, -42, images[theme.key]);
      const scale = Math.max(226 / art.width, 185 / art.height);
      art.setScale(scale).setCrop((art.width - 226 / scale)/2, (art.height - 185 / scale)/2, 226 / scale, 185 / scale);
      if (!available) art.setTint(0x666666);
      const footer = this.add.rectangle(0, 112, 238, 78, available ? 0x362319 : 0x22242a);
      const name = this.add.text(0, 93, labels[theme.key] || theme.label, {
        fontFamily:"Arial",fontStyle:"bold",fontSize:"18px",color:available?"#fff2d9":"#c0c0c0",
        stroke:"#111111",strokeThickness:3,align:"center",wordWrap:{width:220}
      }).setOrigin(.5);
      const subtitle = this.add.text(0, 131, available ? `${theme.rooms.length} aventura${theme.rooms.length === 1 ? "" : "s"}` : "🔒 Próximamente", {
        fontFamily:"Arial",fontSize:"15px",color:available?"#ffca70":"#b8b8b8"
      }).setOrigin(.5);
      card.add([shadow,panel,art,footer,name,subtitle]);
      const hitbox = this.add.rectangle(x, y, 250, 306, 0x000000, 0);
      this.physics.add.existing(hitbox, true);
      hitbox.themeData = theme;
      hitbox.themeAvailable = available;
      this.portals.push(hitbox);
      if (available) {
        hitbox.setInteractive({useHandCursor:true}).on("pointerdown", () => {
          window.location.assign(`/escape/?theme=${encodeURIComponent(theme.key)}`);
        });
        this.tweens.add({targets:panel,alpha:.83,duration:1050,yoyo:true,repeat:-1});
      }
    });
  }

  spreadX(n, margin = 260) {
    const total = 1280;
    if (n <= 0) return [];
    if (n === 1) return [total / 2];
    const step = (total - 2 * margin) / (n - 1);
    return Array.from({ length: n }, (_, i) => margin + i * step);
  }

  update() {
    if (!this.player || !this.player.body) return;
    if (this.overlayOpen) {
      this.player.body.setVelocity(0);
      return;
    }

    const speed = 240;
    const body = this.player.body;
    body.setVelocity(0);

    let nextDir = this.player.currentDir;
    if (this.cursors.left.isDown) {
      body.setVelocityX(-speed);
      nextDir = "left";
    }
    if (this.cursors.right.isDown) {
      body.setVelocityX(speed);
      nextDir = "right";
    }
    if (this.cursors.up.isDown) {
      body.setVelocityY(-speed);
      nextDir = "up";
    }
    if (this.cursors.down.isDown) {
      body.setVelocityY(speed);
      nextDir = "down";
    }

    if (nextDir !== this.player.currentDir) {
      this.player.setTexture("duck-" + nextDir);
      this.player.currentDir = nextDir;
    }

    let active = null;
    for (const portal of this.portals) {
      if (this.physics.overlap(this.player, portal)) {
        active = portal;
        break;
      }
    }
    this.activePortal = active;

    if (active) {
      if (active.themeAvailable) {
        this.hint.setText(
          `▶ Pulsa ENTER para entrar en: ${active.themeData.label}`,
        );
      } else {
        this.hint.setText(`${active.themeData.label} aún no tiene aventuras`);
      }
    } else {
      this.hint.setText("");
    }

    if (
      active &&
      active.themeAvailable &&
      Phaser.Input.Keyboard.JustDown(this.enterKey)
    ) {
      window.location.assign(`/escape/?theme=${encodeURIComponent(active.themeData.key)}`);
    }
  }
}

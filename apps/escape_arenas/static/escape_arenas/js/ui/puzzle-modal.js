// Overlay HTML flotante encima del canvas de Phaser.
// Expone openPuzzleModal(state, handlers) que devuelve una api
// para que RoomScene actualice el modal según respuestas del backend.

export function openPuzzleModal(state, handlers) {
  const { puzzle } = state;
  let hint = state.hint; // mutable: la escena puede sustituirlo con api.setHint()
  const { onSubmit, onHintRequest, onCancel } = handlers;

  // Limpia modal previo si quedara
  const prev = document.getElementById("puzzle-modal");
  if (prev) prev.remove();

  // Backdrop
  const overlay = document.createElement("div");
  overlay.id = "puzzle-modal";
  overlay.style.cssText = `
    position: fixed; inset: 0; background: rgba(0,0,0,0.85);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000; font-family: monospace;`;

  // Panel central
  const panel = document.createElement("div");
  panel.style.cssText = `
    background: radial-gradient(ellipse at 25% 10%,#fff1ca,#efd6a0 50%,#d8b780); border: 10px solid #8a522d; border-radius: 17px;
    padding: 28px 32px; width: 92%; max-width: 760px; max-height: 86vh; overflow-y: auto; color: #35251b;
    box-shadow: 0 10px 40px rgba(0,0,0,0.8); box-sizing: border-box;`;

  // Título
  const titleEl = document.createElement("h2");
  titleEl.textContent = puzzle.title;
  titleEl.style.cssText = "margin: 0 0 12px; color: #5d311c; font-size: 30px; font-family: Georgia,serif; border-bottom: 2px solid #aa7a4e; padding-bottom: 12px;";
  panel.appendChild(titleEl);

  // Intentos
  if (puzzle.max_attempts) {
    const att = document.createElement("div");
    att.textContent = `Intentos: ${puzzle.attempts_used} / ${puzzle.max_attempts}`;
    att.style.cssText = "font-size: 13px; color: #735037; margin-bottom: 16px;";
    panel.appendChild(att);
  } else {
    const spacer = document.createElement("div");
    spacer.style.cssText = "height: 8px;";
    panel.appendChild(spacer);
  }

  // Descripción
  const desc = document.createElement("p");
  desc.textContent = puzzle.description;
  desc.style.cssText =
    "margin: 0 0 20px; font-size: 15px; line-height: 1.5; color: #483121;";
  panel.appendChild(desc);

  // Respuesta (según tipo)
  let getAnswer, inputEl;
  const stageName = (puzzle.title || "").toLowerCase();
  const mechanism = document.createElement("div");
  mechanism.className = "escape-mechanism";
  panel.appendChild(mechanism);
  const makeChoice = (label, click) => {
    const b=document.createElement("button"); b.type="button"; b.textContent=label;
    b.className="escape-mechanism-choice"; b.addEventListener("click",click);
    mechanism.appendChild(b); return b;
  };
  const makeInfo = (value) => {
    const p=document.createElement("p"); p.className="escape-mechanism-info";
    p.textContent=value; mechanism.appendChild(p); return p;
  };
  if (stageName.includes("circuito ancestral")) {
    const switches={A:0,B:0,C:0,D:0};
    const info=makeInfo("Conecta las entradas: (A AND B) AND (C OR D)");
    const buttons={};
    for(const k of Object.keys(switches)) buttons[k]=makeChoice(`${k} · OFF`,()=>{
      switches[k]=1-switches[k]; buttons[k].textContent=`${k} · ${switches[k]?"ON":"OFF"}`;
      buttons[k].classList.toggle("active",!!switches[k]);
      info.textContent=`(A ∧ B) ∧ (C ∨ D) → ${((switches.A&&switches.B)&&(switches.C||switches.D))?1:0}`;
    });
    getAnswer=()=>String(Number(Boolean((switches.A&&switches.B)&&(switches.C||switches.D))));
  } else if (stageName.includes("acceso restringido")) {
    makeInfo("Tablilla rúnica · Energía = 4 · Cristales = 3 · Puerta = Energía × Cristales + 2");
    const display=makeInfo("Código: —"); let code="";
    for(let n=1;n<=9;n++) makeChoice(String(n),()=>{if(code.length<4)code+=n;display.textContent=`Código: ${code}`});
    makeChoice("0",()=>{if(code.length<4)code+="0";display.textContent=`Código: ${code}`});
    makeChoice("⌫ Borrar",()=>{code=code.slice(0,-1);display.textContent=`Código: ${code||"—"}`});
    getAnswer=()=>code;
  } else if (stageName.includes("terminal bloqueada")) {
    makeInfo("SI energia __ 5: ACTIVAR_PORTAL() · Selecciona el operador de comparación.");
    let chosen="";
    for(const op of puzzle.options||["=","==","+="]) makeChoice(op,()=>{
      chosen=op; mechanism.querySelectorAll("button").forEach(b=>b.classList.toggle("active",b.textContent===op));
    });
    getAnswer=()=>chosen;
  } else if (stageName.includes("calibración temporal")) {
    makeInfo("Simula el bucle: 4 iteraciones · +2 unidades por iteración.");
    let count=0, value=0;const output=makeInfo("Iteración 0 / 4 · Energía 0");
    makeChoice("▶ Ejecutar iteración",()=>{if(count<4){count++;value+=2;output.textContent=`Iteración ${count} / 4 · Energía ${value}`}});
    makeChoice("↺ Reiniciar",()=>{count=0;value=0;output.textContent="Iteración 0 / 4 · Energía 0"});
    getAnswer=()=>count===4?String(value):"";
  } else if (stageName.includes("núcleo inestable")) {
    makeInfo("Sensor: temperatura = 12 ° · SI temperatura > 10 → refrigeración; SINO → mantener.");
    let chosen="";
    for(const op of puzzle.options||["refrigeración","mantener"]) makeChoice(op,()=>{
      chosen=op; mechanism.querySelectorAll("button").forEach(b=>b.classList.toggle("active",b.textContent===op));
    });
    getAnswer=()=>chosen;
  } else if (puzzle.type === "MULTIPLE_CHOICE") {
    const optsBox = document.createElement("div");
    puzzle.options.forEach((opt, i) => {
      const label = document.createElement("label");
      label.style.cssText = `
        display: block; padding: 12px; margin-bottom: 8px;
        background: #e6cb96; border: 2px solid #9b7045; border-radius: 4px;
        cursor: pointer; font-size: 15px;`;
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "answer";
      radio.value = opt;
      if (i === 0) radio.checked = true;
      radio.style.marginRight = "10px";
      label.appendChild(radio);
      label.appendChild(document.createTextNode(opt));
      optsBox.appendChild(label);
    });
    panel.appendChild(optsBox);
    getAnswer = () => {
      const c = panel.querySelector('input[name="answer"]:checked');
      return c ? c.value : "";
    };
  } else if (puzzle.type === "SEQUENCE") {
    // The browser receives only the shuffled actions; the solution stays in Django.
    const list = document.createElement("ol");
    list.setAttribute("aria-label", "Orden de acciones");
    list.style.cssText = "list-style:none;padding:0;display:grid;gap:8px";
    const choices = [...(puzzle.sequence_items || [])].sort(() => Math.random() - 0.5);
    const render = () => {
      list.replaceChildren();
      choices.forEach((choice, i) => {
        const row = document.createElement("li");
        row.style.cssText = "display:flex;align-items:center;gap:10px;padding:8px;background:#e6cb96;border-radius:6px";
        const name = document.createElement("span");
        name.textContent = `${i+1}. ${choice}`;
        name.style.flex = "1";
        row.appendChild(name);
        for (const [symbol, delta] of [["↑",-1],["↓",1]]) {
          const b = document.createElement("button");
          b.type = "button"; b.textContent = symbol;
          b.setAttribute("aria-label", `${symbol === "↑" ? "Subir" : "Bajar"} ${choice}`);
          b.disabled = i+delta < 0 || i+delta >= choices.length;
          b.onclick = () => { [choices[i],choices[i+delta]]=[choices[i+delta],choices[i]]; render(); };
          row.appendChild(b);
        }
        list.appendChild(row);
      });
    };
    render(); panel.appendChild(list);
    getAnswer = () => choices.join(",");
  } else {
    inputEl = document.createElement("input");
    inputEl.type = puzzle.type === "NUMBER" ? "number" : "text";
    inputEl.placeholder = "Escribe tu respuesta...";
    inputEl.autocomplete = "off";
    inputEl.style.cssText = `
      width: 100%; padding: 14px; font-size: 18px; background: #fff2cf;
      border: 2px solid #a47a4d; border-radius: 4px; color: #392b1d;
      font-family: monospace; box-sizing: border-box;`;
    panel.appendChild(inputEl);
    getAnswer = () => inputEl.value;
    setTimeout(() => inputEl.focus(), 50);
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") submitBtn.click();
    });
  }

  // Feedback
  const feedback = document.createElement("div");
  feedback.style.cssText =
    "min-height: 24px; margin: 16px 0 10px; text-align: center; font-size: 15px; font-weight: bold;";
  panel.appendChild(feedback);

  // Área donde se insertará el texto de la pista al usarla
  const hintBox = document.createElement("div");
  panel.appendChild(hintBox);

  // Botones
  const btnBar = document.createElement("div");
  btnBar.style.cssText =
    "display: flex; gap: 12px; justify-content: space-between; margin-top: 12px;";

  const mkBtn = (label, bg, color = "#000") => {
    const b = document.createElement("button");
    b.textContent = label;
    b.style.cssText = `
      padding: 12px 20px; font-size: 15px; font-family: monospace;
      background: ${bg}; color: ${color}; border: none; border-radius: 4px;
      cursor: pointer; font-weight: bold;`;
    return b;
  };

  const hintBtn = mkBtn(
    hint ? "💡 Pista" : "Sin pistas",
    hint ? "#64b5f6" : "#555",
    "#fff",
  );
  if (!hint) {
    hintBtn.disabled = true;
    hintBtn.style.cursor = "not-allowed";
    hintBtn.style.opacity = "0.6";
  }
  const cancelBtn = mkBtn("Cancelar", "#755036", "#fff1d4");
  const submitBtn = mkBtn("Enviar ▶", "#b8793d");

  btnBar.appendChild(hintBtn);
  const right = document.createElement("div");
  right.style.cssText = "display: flex; gap: 12px;";
  right.appendChild(cancelBtn);
  right.appendChild(submitBtn);
  btnBar.appendChild(right);
  panel.appendChild(btnBar);

  overlay.appendChild(panel);
  document.body.appendChild(overlay);

  // Keyframes para shake (una sola vez)
  if (!document.getElementById("puzzle-modal-styles")) {
    const style = document.createElement("style");
    style.id = "puzzle-modal-styles";
    style.textContent = `
      @keyframes shake-panel {
        0%, 100% { transform: translateX(0); }
        20% { transform: translateX(-12px); }
        40% { transform: translateX(12px); }
        60% { transform: translateX(-8px); }
        80% { transform: translateX(8px); }
      }`;
    document.head.appendChild(style);
  }

  // ESC cierra
  function onKey(e) {
    if (e.key === "Escape") {
      e.preventDefault();
      api.close();
      onCancel();
    }
  }
  document.addEventListener("keydown", onKey);

  // API expuesta a RoomScene
  const api = {
    showFeedback(text, color) {
      feedback.textContent = text;
      feedback.style.color = color;
    },
    shake() {
      panel.style.animation = "shake-panel 0.4s";
      setTimeout(() => {
        panel.style.animation = "";
      }, 420);
    },
    disable() {
      submitBtn.disabled = true;
      submitBtn.style.opacity = "0.5";
      hintBtn.disabled = true;
      hintBtn.style.opacity = "0.5";
    },
    enable() {
      submitBtn.disabled = false;
      submitBtn.style.opacity = "1";
      if (hint) {
        hintBtn.disabled = false;
        hintBtn.style.opacity = "1";
      }
      if (inputEl) {
        inputEl.focus();
        inputEl.select && inputEl.select();
      }
    },
    appendHintText(text) {
      const h = document.createElement("div");
      h.textContent = "💡 " + text;
      h.style.cssText = `
        margin-top: 8px; padding: 12px; background: #1a2a44;
        border-left: 4px solid #64b5f6; color: #cde; font-size: 14px;
        line-height: 1.5;`;
      hintBox.appendChild(h);
      // La escena decide luego con setHint() si queda otra pista.
    },
    setHint(newHint) {
      hint = newHint;
      if (newHint) {
        hintBtn.disabled = false;
        hintBtn.textContent = "💡 Pista";
        hintBtn.style.opacity = "1";
        hintBtn.style.cursor = "pointer";
        hintBtn.style.backgroundColor = "#64b5f6";
      } else {
        hintBtn.disabled = true;
        hintBtn.textContent = "Sin más pistas";
        hintBtn.style.opacity = "0.6";
        hintBtn.style.cursor = "not-allowed";
        hintBtn.style.backgroundColor = "#555";
      }
    },
    close() {
      document.removeEventListener("keydown", onKey);
      overlay.remove();
    },
  };

  submitBtn.addEventListener("click", () => {
    const ans = getAnswer().toString().trim();
    if (!ans) {
      api.showFeedback("Escribe una respuesta", "#ff9800");
      return;
    }
    onSubmit(ans, api);
  });
  hintBtn.addEventListener("click", () => {
    if (hint) onHintRequest(api);
  });
  cancelBtn.addEventListener("click", () => {
    api.close();
    onCancel();
  });

  return api;
}


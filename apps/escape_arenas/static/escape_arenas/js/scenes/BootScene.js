export default class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  preload() {
    const base = window.DUCKY.staticBase + "img/duck/";
    this.load.image("escape-cueva", window.DUCKY.staticBase + "img/escenarios/cueva.png");
    this.load.image("escape-taller", window.DUCKY.staticBase + "img/escenarios/taller.png");
    this.load.image("escape-portal", window.DUCKY.staticBase + "img/escenarios/portal.png");
    this.load.image("cave-playable-sample", window.DUCKY.staticBase + "img/cave-playable-sample.png");
    this.load.image("duck-down", base + "duck-down.png");
    this.load.image("duck-up", base + "duck-up.png");
    this.load.image("duck-left", base + "duck-left.png");
    this.load.image("duck-right", base + "duck-right.png");
  }

  create() {
    const sessionId = window.DUCKY.initialSession;
    if (sessionId) {
      this.scene.start("RoomScene", {sessionId, escapeRoom:{era:1}, resumed:true});
    } else {
      this.scene.start("HubScene");
    }
  }
}

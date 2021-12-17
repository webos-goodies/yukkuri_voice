const PRESETS = {
  F1: { bas:0, spd:100, vol:100, pit:100, acc:100, lmd:100, fsc:100 },
  F2: { bas:1, spd:100, vol:100, pit:77,  acc:150, lmd:100, fsc:100 },
  F3: { bas:0, spd:80,  vol:100, pit:100, acc:100, lmd:61,  fsc:148 },
  M1: { bas:2, spd:100, vol:100, pit:30,  acc:100, lmd:100, fsc:100 },
  M2: { bas:2, spd:105, vol:100, pit:45,  acc:130, lmd:120, fsc:100 },
  R1: { bas:2, spd:100, vol:100, pit:30,  acc:20,  lmd:190, fsc:100 },
  R2: { bas:1, spd:70,  vol:100, pit:50,  acc:50,  lmd:50,  fsc:180 }
};


class Parameters {

  constructor(formEl, current) {
    this.form    = formEl;
    this.current = current || 1;
    this.timer   = null;
  }

  run() {
    this.loadVoice(this.current);
    this.form.addEventListener('input',  this.valueChanged.bind(this), false);
    this.form.addEventListener('change', this.valueChanged.bind(this), false);
  }

  getAllFields() {
    return this.form.querySelectorAll('input[type=range],select');
  }

  valueChanged(e) {
    this.updateSliderValue(e.target);
    this.startTimer();
  }

  updateSliderValue(el) {
    if(el.tagName.toLowerCase() == 'input' && el.type == 'range') {
      let valueEl = el.parentNode.querySelector('span:last-child');
      valueEl.textContent = '(' + el.value + ')';
    }
  }

  replace(values) {
    this.setValues(values);
    this.stopTimer();
    this.onTimer();
  }

  setValues(values) {
    for(let el of this.getAllFields()) {
      if(el.name in values) {
        el.value = values[el.name];
        this.updateSliderValue(el);
      }
    }
  }

  loadVoice(number) {
    if(this.timer !== null) {
      this.onTimer();
    }

    this.current = number - 0;
    let values = null;
    try {
      let json = localStorage['voice' + this.current];
      if(json) {
        values = JSON.parse(json);
      }
    } catch(e) {}

    if(values) {
      this.setValues(values);
    }
  }

  startTimer() {
    this.stopTimer();
    this.timer = setTimeout(this.onTimer.bind(this), 300);
  }

  stopTimer() {
    if(this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  onTimer() {
    this.timer = null;
    let values = {};
    for(let el of this.getAllFields()) {
      if(el.name) {
        values[el.name] = el.value;
      }
    }
    localStorage['voice' + this.current] = JSON.stringify(values);
  }
}


class Player {

  constructor() {
    this.audio = new Audio();
    this.url   = null;
  }

  play(blob) {
    if(this.url) {
      this.audio.pause();
      this.audio.src = '';
      URL.revokeObjectURL(this.url);
      this.url = null;
    }
    this.url = URL.createObjectURL(blob);
    this.audio.src = this.url;
    this.audio.play();
  }

}


class Downloader {

  constructor() {
    this.url = null;
  }

  download(headers, blob) {
    let filename = 'yukkuri.wav';
    for(let item of (headers.get('Content-Disposition') || '').split(';')) {
      let m = /^\s*filename=['"]?([^\s'"]+)/.exec(item);
      if(m) {
        filename = decodeURIComponent(m[1]);
      }
    }

    if(this.url) {
      URL.revokeObjectURL(this.url);
      this.url = null;
    }
    this.url    = URL.createObjectURL(blob);
    let el      = document.createElement('a');
    el.href     = this.url;
    el.download = filename;
    el.click();
  }

}


class App {

  constructor(root) {
    this.root       = root;
    this.form       = root.querySelector('form.parameters');
    this.text       = this.form.querySelector('textarea[name=text]');
    this.native     = this.form.querySelector('input[name=native]');
    this.current    = (localStorage.currentVoice || 1) - 0;
    this.parameters = new Parameters(this.form, this.current);
    this.player     = new Player();
    this.downloader = new Downloader();
  }

  run() {
    let voicesEl = this.root.querySelector('.voices');
    for(let el of voicesEl.querySelectorAll('input')) {
      if(el.name == 'voice' && el.value == this.current) {
        el.checked = true;
      }
    }
    this.text.value     = localStorage.speechText || '';
    this.native.checked = !!((localStorage.native || 0) - 0);
    this.parameters.run();
    voicesEl.addEventListener('change', this.onVoiceChanged.bind(this), false);
    this.form.addEventListener('submit', this.onPlay.bind(this), false);
    this.text.addEventListener('change', this.onSave.bind(this), false);
    this.native.addEventListener('change', this.onSave.bind(this), false);
    this.root.querySelector('.download a').
      addEventListener('click', this.onDownload.bind(this), false);
    this.root.querySelector('.presets').
      addEventListener('click', this.onPresets.bind(this), false);
  }

  requestWav() {
    return fetch('talk', {
      mode:        'same-origin',
      method:      'POST',
      credentials: 'same-origin',
      cache:       'no-store',
      body:        new FormData(this.form)
    });
  }

  async play() {
    let rsp = await this.requestWav();
    if(rsp.ok) {
      this.player.play(await rsp.blob());
    }
  }

  onPlay(e) {
    e.preventDefault();
    this.play();
  }

  async download() {
    let rsp = await this.requestWav();
    if(rsp.ok) {
      this.downloader.download(rsp.headers, await rsp.blob());
    }
  }

  onDownload(e) {
    e.preventDefault();
    this.download();
  }

  onPresets(e) {
    let values = PRESETS[e.target.value];
    if(values) {
      let msg = e.target.textContent + 'で上書きします。よろしいですか？';
      if(confirm(msg)) {
        this.parameters.replace(values);
      }
    }
  }

  onVoiceChanged(e) {
    if(e.target.name == 'voice') {
      this.current = this.root.querySelector('form.voices').voice.value - 0;
      this.parameters.loadVoice(this.current);
      localStorage.currentVoice = this.current;
    }
  }

  onSave(e) {
    localStorage.speechText = this.text.value;
    localStorage.native = this.native.checked ? 1 : 0;
  }

}


(new App(document)).run();

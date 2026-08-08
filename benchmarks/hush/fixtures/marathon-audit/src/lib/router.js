'use strict';

class Router {
  constructor() {
    this.stack = [];
    this.middleware = [];
  }
  use(fn) { this.middleware.push(fn); }
  get(p, h) { this.stack.push({ method: 'GET', path: p, handler: h }); }
  post(p, h) { this.stack.push({ method: 'POST', path: p, handler: h }); }
}

module.exports = { Router };

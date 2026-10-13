function isInApp() {
  return /com\.bytedance\.homed/i.test(window.navigator.userAgent);
}

function judgeEnvUrl(dom, url) {
  if(isInApp) {
    dom.setAttribute('href', url);
  }
}
(function () {
  function textOf(el) {
    return (el.innerText || "").trim();
  }

  function popoversFor(triggerText) {
    var popovers = Array.prototype.slice.call(
      document.querySelectorAll("div.byted-popover-wrapper"),
    );
    if (triggerText === "了解住小帮") {
      return popovers.filter(function (pop) {
        return (
          /关于我们/.test(pop.innerText) &&
          /装修锦囊/.test(pop.innerText) &&
          /居住研究院/.test(pop.innerText)
        );
      });
    }
    if (triggerText === "业务合作") {
      return popovers.filter(function (pop) {
        return /商家入驻/.test(pop.innerText);
      });
    }
    if (triggerText === "下载APP") {
      return popovers.filter(function (pop) {
        return /扫描二维码下载APP/.test(pop.innerText);
      });
    }
    return [];
  }

  function showPopover(pop, trigger) {
    var rect = trigger.getBoundingClientRect();
    pop.style.display = "block";
    pop.style.visibility = "visible";
    pop.style.opacity = "1";
    pop.style.position = "fixed";
    pop.style.left = Math.max(0, rect.left) + "px";
    pop.style.top = rect.bottom + 4 + "px";
    pop.style.zIndex = "9999";
  }

  function hidePopover(pop) {
    pop.style.display = "none";
  }

  function init() {
    document.querySelectorAll("span.byted-popper-trigger").forEach(function (trigger) {
      var label = textOf(trigger);
      if (label !== "了解住小帮" && label !== "业务合作" && label !== "下载APP") {
        return;
      }

      var pops = popoversFor(label);
      var hideTimer = null;

      function open() {
        if (hideTimer) clearTimeout(hideTimer);
        pops.forEach(function (pop) {
          showPopover(pop, trigger);
        });
      }

      function closeSoon() {
        if (hideTimer) clearTimeout(hideTimer);
        hideTimer = setTimeout(function () {
          pops.forEach(hidePopover);
        }, 160);
      }

      trigger.addEventListener("mouseenter", open);
      trigger.addEventListener("mouseleave", closeSoon);
      trigger.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        open();
      });

      pops.forEach(function (pop) {
        pop.addEventListener("mouseenter", function () {
          if (hideTimer) clearTimeout(hideTimer);
        });
        pop.addEventListener("mouseleave", closeSoon);
        pop.querySelectorAll("a").forEach(function (link) {
          link.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            if (link.href) window.location.href = link.href;
          });
        });
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
  setTimeout(init, 800);
})();

self.addEventListener("install", function () {
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(self.clients.claim());
});

function mockFor(url) {
  var path = new URL(url).pathname;
  if (path.indexOf("/homed/business/") !== -1) {
    if (
      path.indexOf("navibarButtons") !== -1 ||
      path.indexOf("queryRouteList") !== -1 ||
      path.indexOf("newFunctionsGuide") !== -1 ||
      path.indexOf("enumlist") !== -1 ||
      path.indexOf("message/recent") !== -1 ||
      path.indexOf("queryBySubjectIds") !== -1
    ) {
      return { code: 0, data: [] };
    }
    if (path.indexOf("phoneInit") !== -1 || path.indexOf("mobileinfo/get") !== -1) {
      return { code: 0, data: { employee_id: "1" } };
    }
    if (path.indexOf("getSignStatus") !== -1) {
      return { code: 0, data: { signed: true } };
    }
    if (path.indexOf("has_im") !== -1) {
      return { code: 0, data: false };
    }
    return { code: 0, data: {} };
  }
  if (path.indexOf("/homed/api/") !== -1 && path.indexOf("getNgccSign") !== -1) {
    return { code: 0, data: "mock" };
  }
  if (path.indexOf("/passport/") !== -1) {
    return { code: 0, data: [] };
  }
  return null;
}

self.addEventListener("fetch", function (event) {
  var mock = mockFor(event.request.url);
  if (!mock) return;
  event.respondWith(
    new Response(JSON.stringify(mock), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
});

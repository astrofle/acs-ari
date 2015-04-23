var API;

function connect() {
    var communicator = Ice.initialize();
    var hostname = "192.168.1.111";
    var endpoint = "API:ws -h " + hostname + " -p 10002:wss -h " + hostname + " -p 10003";
    console.log("endpoint = " + endpoint);
    var proxy = communicator.stringToProxy(endpoint);
    API = ARIAPI.APIPrx.uncheckedCast(proxy);
};

$(document).ready(function() {
  console.log("llegue");
  connect();

  $("#btGetStatus").click( function(event) {
    event.preventDefault();
    console.log("clicked");
    var communicator = Ice.initialize();
    var hostname = "192.168.1.111";
    var endpoint = "API:ws -h " + hostname + " -p 10002:wss -h " + hostname + " -p 10003";
    console.log("endpoint = " + endpoint);
    var proxy = communicator.stringToProxy(endpoint);
    var obj = ARIAPI.APIPrx.uncheckedCast(proxy);
    API.sayHello().then(
        function() { console.log("sayHello done!"); }
    ).exception(
        function(ex) { console.log("something went wrong!"); }
    ).finally(
        function() { return communicator.destroy(); }
    );

  });
});



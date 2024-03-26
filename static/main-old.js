(function () {
  var client = ZAFClient.init();
  client.invoke('resize', { width: '100%', height: '300px' });
  client.get('ticket.requester.id').then(function(data){
    var user_id = data['ticket.requester.id'];
    requestUserInfo(client,user_id);
  }, function(){
    console.log("Request for ticket.requester.id failed.")
  }
  );
})();

function showInfo(data) {
  var requester_data = {
    'name': data.user.name,
    'tags': data.user.tags,
    'created_at': formatDate(data.user.created_at),
    'last_login_at': formatDate(data.user.last_login_at)
  };
  console.debug("now in showInfo()")
  console.log(data)
  var source = document.getElementById("requester-template").innerHTML;
  var template = Handlebars.compile(source);
  var html = template(requester_data);
  document.getElementById("example").innerHTML = html;
}

function showError(response) {
  var error_info = {
    'status': 404,
    'statusText': "Info not found."
    }

  var source = document.getElementById("error-template").innerHTML;
  var template = Handlebars.compile(source);
  var html = template(response);
  document.getElementById("example").innerHTML = html;
}

function requestUserInfo(client, id) {
  var settings = {
    url: "/api/v2/users/" + id + ".json",
    type: "GET",
    dataType: "json"
  };
  client.request(settings).then(
    function(data){
      showInfo(data);
    },
    function(response){
      showError(response);
    }
  )
}

function formatDate(date){
  var cdate = new Date(date);
  var options = {
    year: "numeric",
    month: "short",
    day: "numeric"
  };
  date = cdate.toLocaleDateString("en-sg", options)

  return date
}
function init() {
  const client = ZAFClient.init(); 
  // const contentHeight = document.getElementById("container-div").offsetHeight;
  console.log(contentHeight);
  var msg = "failure"
  switch (action) { 
    case "notifySuccess": client.invoke("notify", "Request successful!"); 
    break; 
    case "notifyFailure": client.invoke("notify", msg, "error"); 
    console.log(client);
    console.log(msg);
    break; 
    case "resize": client.invoke('resize', { width: '100%', height: contentHeight + 40 });
    console.log(client);
    break;
    case "comment": client.invoke('ticket.comment.appendText', "yello");
    console.log("commented")
    break;
  } 
}

window.addEventListener("load", init, false);
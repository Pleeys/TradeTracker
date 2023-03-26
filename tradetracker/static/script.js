let btn = document.querySelector('#btn');
let sidebar = document.querySelector('.sidebar');
let trade_tracker_logo = document.querySelector('.trade_tracker_logo');

btn.onclick = function () {
    sidebar.classList.toggle('active');
    trade_tracker_logo.classList.toggle('active');
    
};

var cPass = document.getElementById("c-pass");
cPass.textContent = cPass.textContent.replace("_", " ");


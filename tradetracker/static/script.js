let btn = document.querySelector('#btn');
let sidebar = document.querySelector('.sidebar');
let trade_tracker_logo = document.querySelector('.trade_tracker_logo');
let navbar_right = document.querySelector('.navbar-right');

btn.onclick = function () {
    sidebar.classList.toggle('active');
    trade_tracker_logo.classList.toggle('active');
    navbar_right.classList.toggle('active');
};




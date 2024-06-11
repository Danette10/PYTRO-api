const listButtonCloseModal =
  document.getElementsByClassName("button-close-modal");
const listButtonLoginAccount = document.getElementsByClassName(
  "button-login-account"
);
const listButtonCreateAccount = document.getElementsByClassName(
  "button-create-account"
);

const modalLogin = document.getElementById("modal-login");
const modalRegister = document.getElementById("modal-register");

for (let button of listButtonCloseModal) {
  button.addEventListener("click", function () {
    let containerDiv = this.parentElement;
    let container = containerDiv.parentElement;

    container.classList.remove("display-flex");
    container.classList.add("display-hidden");
  });
}

for (let button of listButtonLoginAccount) {
  button.addEventListener("click", function () {
    modalLogin.classList.remove("display-hidden");
    modalRegister.classList.add("display-hidden");
  });
}

for (let button of listButtonCreateAccount) {
  button.addEventListener("click", function () {
    modalRegister.classList.remove("display-hidden");
    modalLogin.classList.add("display-hidden");
  });
}

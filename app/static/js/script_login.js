document.addEventListener("DOMContentLoaded", function () {
  const status = document.getElementById("status")

  // olha o ?error= na URL
  const params = new URLSearchParams(window.location.search)
  const error = params.get("error")

  if (error) {
    let msg
    switch (error) {
      case "unauthorized":
        msg = "Seu e-mail não está autorizado a gerar relatórios."
        break
      case "email_not_verified":
        msg = "Por favor, verifique seu e-mail no Google antes de continuar."
        break
      default:
        // se veio outro texto, exibe cru
        msg = decodeURIComponent(error)
    }
    status.textContent = msg
    status.classList.remove("hidden")
    status.classList.add("error-message")
  }
})

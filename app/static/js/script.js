document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("report-form")
  const status = document.getElementById("status")
  const fileNameDisplay = document.getElementById("file-name")
  const downloadSection = document.getElementById("download-section")
  const downloadButton = document.getElementById("download-button")
  const logoutLink = document.getElementById("logout-link")
  const buttonSubmit = document.getElementById("submit-button")

  let downloadUrl = ""
  let controller = null

  form.addEventListener("submit", async function (e) {
    e.preventDefault()

    buttonSubmit.disabled = true
    buttonSubmit.classList.add('noHover')

    console.log('clicado')

    const startDate = document.getElementById("start-date").value
    const endDate = document.getElementById("end-date").value

    // Limpa classes anteriores
    status.className = ""
    downloadSection.classList.add("hidden")

    try {
      // Validações das datas
      if (!startDate || !endDate) {
        throw new Error("Preencha ambas as datas.")
      }

      if (new Date(startDate) > new Date(endDate)) {
        throw new Error("Data inicial não pode ser depois da final.")
      }

      const today = new Date()
      if (new Date(startDate) > today || new Date(endDate) > today) {
        throw new Error("Data não pode ser maior que hoje.")
      }

      // Validação de intervalo máximo de 6 meses (aproximadamente 183 dias)
      const maxEndDate = new Date(startDate)
      maxEndDate.setMonth(maxEndDate.getMonth() + 6)

      if (new Date(endDate)> maxEndDate) {
        throw new Error("O intervalo entre as datas não pode ser maior que 6 meses.")
      }

      // Se passou pelas validações:
      status.textContent = "Gerando relatório..."
      status.classList.remove("hidden")
      status.classList.add("success-message")

      const response = await fetch(
        `/report/download?start_date=${startDate}&end_date=${endDate}`
      )

      if (!response.ok) throw new Error("Erro ao gerar relatório.")

      const blob = await response.blob()
      downloadUrl = window.URL.createObjectURL(blob)
      const fileName = `relatorio_${startDate}_ate_${endDate}.xlsx`

      fileNameDisplay.textContent = fileName
      downloadSection.classList.remove("hidden")
      status.classList.add("hidden")
      buttonSubmit.disabled = false
      buttonSubmit.classList.remove('noHover')

    } catch (err) {
      showError(err.message || "Erro ao gerar o relatório.")
      buttonSubmit.disabled = false
      buttonSubmit.classList.remove('noHover')
    }
  })

  downloadButton.addEventListener("click", function () {
    if (downloadUrl) {
      const a = document.createElement("a")
      a.href = downloadUrl
      a.download = fileNameDisplay.textContent
      a.click()
    }
  })

  logoutLink.addEventListener("click", function () {
    // 1) aborta qualquer fetch em andamento
    if (controller) controller.abort()
    // 2) desabilita o form para evitar novos envios
    form.querySelector("button[type=submit]").disabled = true
    // (o redirect do Flask para /auth/login acontece logo em seguida)
  })

  function showError(message) {
    status.textContent = message
    status.className = "error-message"
    status.classList.remove("hidden")
  }
})

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000"

class ApiService {
  async runTiering(data) {
    const response = await fetch(`${API_BASE_URL}/run-tiering`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async getHeatmap(analysisId) {
    const response = await fetch(`${API_BASE_URL}/heatmap/${analysisId}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.blob()
  }

  async getResults(analysisId) {
    const response = await fetch(`${API_BASE_URL}/results/${analysisId}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async saveSettings(settings) {
    const response = await fetch(`${API_BASE_URL}/settings`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(settings),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async getSettings() {
    const response = await fetch(`${API_BASE_URL}/settings`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async uploadFile(file) {
    const formData = new FormData()
    formData.append("file", file)

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }
}

export default new ApiService()

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000"

class ApiService {
  // 🔹 Run tiering analysis (includes API key from saved settings)
  async runTiering(data) {
    try {
      // Get the user's saved settings (e.g., API key)
      const settings = await this.getSettings()
      const apiKey = settings.api_key || null

      const payload = {
        ...data,
        api_key: apiKey, // Inject API key into analysis request
      }

      const response = await fetch(`${API_BASE_URL}/run-tiering`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return response.json()
    } catch (error) {
      console.error("runTiering error:", error)
      throw error
    }
  }

  // 🔹 Get analysis heatmap image (returns blob)
  async getHeatmap(analysisId) {
    const response = await fetch(`${API_BASE_URL}/heatmap/${analysisId}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.blob()
  }

  // 🔹 Get tiering results
  async getResults(analysisId) {
    const response = await fetch(`${API_BASE_URL}/results/${analysisId}`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  // 🔹 Save LLM configuration settings (LLM type, API key, etc.)
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

  // 🔹 Load saved LLM/API settings
  async getSettings() {
    const response = await fetch(`${API_BASE_URL}/settings`)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  // 🔹 Upload .ndjson log file
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
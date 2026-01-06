import axios from 'axios';

// Use environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const pdfService = {
  // Fetch all PDFs from the input folder
  getAllPDFs: async () => {
    try {
      const response = await api.get('/pdfs');
      return response.data;
    } catch (error) {
      console.error('Error fetching PDFs:', error);
      throw error;
    }
  },

  // Get PDFs grouped by category
  getPDFsByCategory: async () => {
    try {
      const response = await api.get('/pdfs/by-category');
      return response.data;
    } catch (error) {
      console.error('Error fetching PDFs by category:', error);
      throw error;
    }
  },

  // Extract three statements from a PDF
  extractStatements: async (pdfId) => {
    try {
      const response = await api.post(`/pdfs/${pdfId}/extract`);
      return response.data;
    } catch (error) {
      console.error('Error extracting statements:', error);
      throw error;
    }
  },

  // Submit selected statements
  submitSelectedStatements: async (pdfId, selectedStatements) => {
    try {
      const response = await api.post(`/pdfs/${pdfId}/submit`, {
        selectedStatements,
      });
      return response.data;
    } catch (error) {
      console.error('Error submitting statements:', error);
      throw error;
    }
  },

  // Extract data from selected pages
  extractDataFromPages: async (pdfId, selectedPages) => {
    try {
      const response = await api.post(`/pdfs/${pdfId}/extract-data`, {
        selectedPages,
      });
      return response.data;
    } catch (error) {
      console.error('Error extracting data from pages:', error);
      throw error;
    }
  },
};

export default api;

import axios from "axios";


const serverAddress = "http://localhost:8711"

export const url = {
    startEntropySearch: (data) => axios.post(`${serverAddress}/entropy_search`, data),
    getStatus: () => axios.get(`${serverAddress}/get/status`),
    getAllSpectra: () => axios.get(`${serverAddress}/get/all_spectra`),
    getOneSpectrum: (scan) => axios.get(`${serverAddress}/get/one_spectrum/${scan}`),
}
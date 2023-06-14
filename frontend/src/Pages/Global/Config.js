import axios from "axios";


const serverAddress = "http://localhost:8711"

export const url = {
    getCpuCores: () => axios.get(`${serverAddress}/get/cpu`),
    startEntropySearch: (data) => axios.post(`${serverAddress}/entropy_search`, data),
    getStatus: () => axios.get(`${serverAddress}/get/status`, { timeout: 800 }),
    getAllSpectra: () => axios.get(`${serverAddress}/get/all_spectra`),
    getOneSpectrum: (scan) => axios.get(`${serverAddress}/get/one_spectrum/${scan}`),
    getOneLibrarySpectrum:(charge,idx)=>axios.get(`${serverAddress}/get/one_library_spectrum/${charge}/${idx}`),
}
export const API_BASE = "http://127.0.0.1:8000";

export function authHeader() {
    const token = localStorage.getItem("token");
    return {
        "Authorization": `Token ${token}`     // <-- if backend uses JWT change to Bearer
    };
}

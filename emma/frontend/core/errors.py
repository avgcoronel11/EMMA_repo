class ApiClientError(Exception):
    def __init__(self, status_code=None, detail="", payload=None):
        self.status_code = status_code
        self.detail = detail
        self.payload = payload or {}
        self.error = self.payload.get("error", {})
        super().__init__(detail)


def to_user_message(error):
    if error.error.get("mensaje"):
        return error.error["mensaje"]
    if error.status_code == 400:
        return "La informacion enviada no es valida."
    if error.status_code == 401:
        return "La sesion no esta autorizada para consultar esta informacion."
    if error.status_code == 403:
        return "No tienes permisos para realizar esta accion."
    if error.status_code == 404:
        return "El recurso solicitado no existe."
    if error.status_code and error.status_code >= 500:
        return "La API no pudo procesar la solicitud."
    return "No fue posible comunicarse con la API."


def form_errors_from_api(error):
    detalles = error.error.get("detalles")
    if isinstance(detalles, dict) and detalles:
        return detalles
    return {"__all__": [to_user_message(error)]}

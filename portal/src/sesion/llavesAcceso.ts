// Llaves de acceso (WebAuthn): convierte las opciones JSON del servidor (base64url) al formato del
// navegador y la credencial resultante de vuelta a JSON, sin dependencias externas.

type Json = Record<string, unknown>;

function aBytes(base64url: string): ArrayBuffer {
  const base64 = base64url.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(base64url.length / 4) * 4, "=");
  const binario = atob(base64);
  const bytes = new Uint8Array(binario.length);
  for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i);
  return bytes.buffer;
}

function aBase64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binario = "";
  bytes.forEach((b) => (binario += String.fromCharCode(b)));
  return btoa(binario).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function llavesDisponibles(): boolean {
  return typeof window !== "undefined" && "PublicKeyCredential" in window && !!navigator.credentials;
}

function convertirLista(lista: unknown): PublicKeyCredentialDescriptor[] | undefined {
  if (!Array.isArray(lista)) return undefined;
  return lista.map((c: Json) => ({ ...(c as object), id: aBytes(String(c.id)) }) as PublicKeyCredentialDescriptor);
}

export async function crearLlave(opciones: Json): Promise<Json> {
  const publicKey = {
    ...opciones,
    challenge: aBytes(String(opciones.challenge)),
    user: { ...(opciones.user as Json), id: aBytes(String((opciones.user as Json).id)) },
    excludeCredentials: convertirLista(opciones.excludeCredentials)
  } as unknown as PublicKeyCredentialCreationOptions;
  const credencial = (await navigator.credentials.create({ publicKey })) as PublicKeyCredential | null;
  if (!credencial) throw new Error("No se creó la llave de acceso.");
  const respuesta = credencial.response as AuthenticatorAttestationResponse;
  return {
    id: credencial.id,
    rawId: aBase64url(credencial.rawId),
    type: credencial.type,
    response: {
      clientDataJSON: aBase64url(respuesta.clientDataJSON),
      attestationObject: aBase64url(respuesta.attestationObject),
      transports: respuesta.getTransports?.() ?? []
    },
    clientExtensionResults: credencial.getClientExtensionResults?.() ?? {}
  };
}

export async function usarLlave(opciones: Json): Promise<Json> {
  const publicKey = {
    ...opciones,
    challenge: aBytes(String(opciones.challenge)),
    allowCredentials: convertirLista(opciones.allowCredentials)
  } as unknown as PublicKeyCredentialRequestOptions;
  const credencial = (await navigator.credentials.get({ publicKey })) as PublicKeyCredential | null;
  if (!credencial) throw new Error("No se usó ninguna llave de acceso.");
  const respuesta = credencial.response as AuthenticatorAssertionResponse;
  return {
    id: credencial.id,
    rawId: aBase64url(credencial.rawId),
    type: credencial.type,
    response: {
      clientDataJSON: aBase64url(respuesta.clientDataJSON),
      authenticatorData: aBase64url(respuesta.authenticatorData),
      signature: aBase64url(respuesta.signature),
      userHandle: respuesta.userHandle ? aBase64url(respuesta.userHandle) : null
    },
    clientExtensionResults: credencial.getClientExtensionResults?.() ?? {}
  };
}

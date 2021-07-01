"""
    Fichero:
        encryption.py
    Autores:
        Antonio Altea Segovia
        Raul Cuesta Barroso
    Asignatura: 
        Redes-II
    Grupo:
        2311
    Pareja:
        14
"""


from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import PKCS1_OAEP
from base64 import b64decode, b64encode

__PRIVATE_KEY_FILE = 'private.pem'
__PUBLIC_KEY_FILE = 'public.pem'

IV_SIZE = 16
R_KEY_SIZE = 32
CSK_SIZE = 256

def generate_keys():
    """
    Encargado de generar las claves pública y privadas RSA almacenarlas en sus
    correspondientes ficheros
    
    """

    # Genera las claves
    key = RSA.generate(2048)

    # Clave privada
    with open(__PRIVATE_KEY_FILE, 'wb') as f_private:
        f_private.write(key.export_key('PEM'))
    f_private.close()

    # Clave pública
    with open(__PUBLIC_KEY_FILE, 'wb') as f_public:
        f_public.write(key.public_key().export_key('PEM'))
    f_public.close()


def read_public_key():
    """
    Lee la clave pública de su fichero

    Retuns:
        Clave pública
    """

    with open('public.pem', 'rb') as f:
        key = RSA.import_key(f.read())
    f.close()
    return key


def read_private_key():
    """
    Lee la clave privada de su fichero

    Retuns:
        Clave privada
    """
    
    with open('private.pem', 'rb') as f:
        key = RSA.import_key(f.read())
    f.close()
    return key


def sign_file_content(file_content):
    """
    Firma un determinado string

    Parámetros:
        file_content (str): String a firmar 
    """

    private_key = read_private_key()

    hash = SHA256.new(file_content)         # objeto hash del contenido del fichero
    signer = pkcs1_15.new(private_key)      # objeto signer para crear la firma
    signature = signer.sign(hash)           # creación de la firma

    return signature + file_content # devolvemos el contenido concatenado a la firma


def enc_file_content(file_content, dest_key):
    """
    Encripta un determinado string con el método CBC y AES

    Parametros:
        file_content(str): String a encriptar
        dest_key (key): clave pública del usuario destino

    Returns:
        (str) vecto de inicialización + clave de sisión cifrada + contenido cifrado
    """

    iv = get_random_bytes(IV_SIZE)          # vector de inicialización aleatorio
    r_key = get_random_bytes(R_KEY_SIZE)    # clave de sesión aleatoria

    # cifrador AES con la clave de sesión
    cipher = AES.new(r_key, AES.MODE_CBC, iv)
    # encriptamos el contenido con la clave de sesión
    ct_bytes = cipher.encrypt(pad(file_content, AES.block_size))

    # cifrador con la clave pública del destino
    cipher_r_key = PKCS1_OAEP.new(RSA.import_key(dest_key))
    # ciframos la clave de sesión con la clave pública del destino
    ct_r_key = cipher_r_key.encrypt(r_key)

    # devolvemos el vector de inicialización junto con la clave de sesión cifrada
    # y el contenido cifrado
    return iv + ct_r_key + ct_bytes


def decrypt_file_content(file_content, source_key):
    """
    Desncripta un determinado string con el método CBC y AES

    Parametros:
        file_content(str): String a desencriptar
        source_key (key): clave pública del usuario fuente

    Returns:
        (str) mensaje desencriptado
    """

    # obtenemos el vector de inicialización
    iv = file_content[:IV_SIZE]
    # obtenemos la clave de sesión cifrada
    ct_r_key = file_content[IV_SIZE:IV_SIZE+CSK_SIZE]
    # obtenemos el contenido cifrado
    s_content = file_content[IV_SIZE+CSK_SIZE:]

    # cifrador de nuestra clave privada
    cipher_r_key = PKCS1_OAEP.new(read_private_key())
    # obtenemos la clave de sisión
    r_key = cipher_r_key.decrypt(ct_r_key)

    # cifrador de la clave de sesión
    cipher = AES.new(r_key, AES.MODE_CBC, iv)
    # desencriptado
    decrypted_pad = cipher.decrypt(s_content)
    decrypted = unpad(decrypted_pad, AES.block_size)

    # extraemos la firma y el mensaje
    sign = decrypted[:CSK_SIZE]
    message = decrypted[CSK_SIZE:]

    # verificamos que la firma es correcta
    digest = SHA256.new()
    digest.update(message)
    signer = pkcs1_15.new(RSA.import_key(source_key))

    try:
        signer.verify(digest, sign)
        print("Firma verificada")
    except Exception as e:
        print("Error al verificar la firma")
        exit()

    return message


def enc_sign_content(file_content, dest_key):
    """
    Función que firma y encripta un String dado

    Parámetros:
        file_content(str): String a firmar y encriptar
        dest_key (str): clave pública destino para el encriptado
    """
    signed = sign_file_content(file_content)
    return enc_file_content(signed, dest_key)

import imaplib
import email
from email.header import decode_header
from tqdm import tqdm
import datetime
import getpass

IMAP_SERVER = "imap.gmail.com"
PORT = 993

def conect_email(email_user, password):
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, PORT)
        mail.login(email_user, password)
        print("[✓] Login realizado!")
        return mail
    except Exception as e:
        print(f"[X] Erro ao conectar: {e}")
        return None
    

def labels_list(mail):
    print("\n[Pastas disponíveis no seu Gmail:]\n")
    status, pastas = mail.list()
    if status == "OK":
        for pasta in pastas:
            print(pasta.decode())

def select_folder(mail, folder_name):
    status, _ = mail.select(f'"{folder_name}"')
    if status != "OK":
        print(f"[X] Erro ao acessar a pasta: {folder_name}")
        return False
    return True

def find_old_emails(mail, dias=30):
    limit_date = (datetime.datetime.now() - datetime.timedelta(days=dias)).strftime("%d-%b-%Y")
    status, dados = mail.search(None, f'BEFORE {limit_date}')
    if status != 'OK':
        print("[X] Erro ao buscar e-mails")
        return []
    return dados[0].split()

def show_emails(mail, lista_ids, limit=15):
    print("\n[E-mails encontrados]")
    for i, num in enumerate(lista_ids[:limit]):
        _, dados = mail.fetch(num, "(RFC822)")
        raw_email = dados[0][1]
        msg = email.message_from_bytes(raw_email)

        assunto, _ = decode_header(msg["Subject"])[0]
        if isinstance(assunto, bytes):
            assunto = assunto.decode(errors="ignore")
        
        de = msg.get("From")

        print(f"-> {i+1}. Assunto: {assunto} | De: {de}")
    if len(lista_ids) > limit:
        print(f"... e mais {len(lista_ids) - limit} e-mails.")

def delete_emails(mail, lista_ids, chunk_size=200):
    if not lista_ids:
        print("[!] Nenhum email para deletar.")
        return

    print(f"[!] Deletando {len(lista_ids)} e-mails em blocos de {chunk_size}...")

    lista_ids = [id.decode() if isinstance(id, bytes) else id for id in lista_ids]

    for i in tqdm(range(0, len(lista_ids), chunk_size), desc="Progresso", unit="bloco"):
        chunk = lista_ids[i:i + chunk_size]
        ids_str = ','.join(chunk)
        mail.store(ids_str, '+FLAGS', '\\Deleted')
    mail.expunge()
    print("[✓] E-mails deletados com sucesso.")


def main():
    print("== LIMPEZA DE EMAILS ==")
    email_user = input("Digite seu email Gmail: ")
    password = getpass.getpass("Digite sua senha ou senha de app: ")


    mail = conect_email(email_user, password)
    if not mail:
        return
    
    labels_list(mail)
    name_folder = input("\nCOpie e cole o nome da pasta que deseja acessar (ex: [Gmail]/Promoções): ")
    if not select_folder(mail, name_folder):
        return
    
    dias = int(input("Buscar emails com mais de quantos dias? (ex:60): "))
    lista_ids = find_old_emails(mail, dias)

    print(f"\n→ {len(lista_ids)} e-mails encontrados com mais de {dias} dias na pasta '{name_folder}'.")

    if lista_ids:
        show_emails(mail, lista_ids)
        confirm = input("\nDeseja deletar esses e-mails? (s/n): ")
        if confirm.lower() == "s":
            delete_emails(mail, lista_ids)
        else:
            print("[!] Operação cancelada.")
    else:
        print("[!] Nenhum email encontrado com os critérios definidos.")

    mail.logout()

if __name__ == "__main__":
    main()
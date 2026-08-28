# import subprocess

# def generate_api_token_with_openssl():
#     result = subprocess.run(
#         ["openssl", "rand", "-base64", "32"],
#         capture_output=True,
#         text=True,
#         check=True,
#     )
#     tunnel_secret = result.stdout.strip()
#
#     return tunnel_secret

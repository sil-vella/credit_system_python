from .vault_secrets import vault_secrets
import os

def check_secrets_health():
    """
    Check the health of the secrets management system
    
    Returns:
        dict: Health status of different secret management components
    """
    status = {
        "vault": {
            "healthy": vault_secrets.is_healthy(),
            "available": bool(os.getenv('VAULT_ADDR'))
        },
        "docker_secrets": {
            "available": os.path.exists('/run/secrets')
        }
    }
    
    status["overall"] = (
        status["vault"]["healthy"] or 
        status["docker_secrets"]["available"]
    )
    
    return status 
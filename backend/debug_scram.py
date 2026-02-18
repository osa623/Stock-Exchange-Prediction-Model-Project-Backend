"""Debug SCRAM-SHA-256 handshake with CosmosDB."""
import pymongo.auth as auth_module
import pymongo.pool
import base64

# Monkey-patch to intercept SCRAM conversation
_orig_command = pymongo.pool.SocketInfo.command

def debug_command(self, dbname, spec, *args, **kwargs):
    is_sasl = "saslStart" in spec or "saslContinue" in spec
    if is_sasl:
        print("=== CMD to %s ===" % dbname)
        for k, v in spec.items():
            if isinstance(v, bytes):
                print("  %s: %s" % (k, v.decode("utf-8", errors="replace")))
            else:
                print("  %s: %s" % (k, v))
    try:
        result = _orig_command(self, dbname, spec, *args, **kwargs)
        if is_sasl:
            print("=== RESPONSE ===")
            for k, v in result.items():
                if isinstance(v, bytes):
                    print("  %s: %s" % (k, v.decode("utf-8", errors="replace")))
                else:
                    print("  %s: %s" % (k, v))
        return result
    except Exception as e:
        if is_sasl:
            print("=== ERROR: %s ===" % e)
        raise

pymongo.pool.SocketInfo.command = debug_command

from pymongo import MongoClient

url = (
    "mongodb+srv://serveradmin:BaosWheels623@"
    "buyzonlabscluster.global.mongocluster.cosmos.azure.com/"
    "?tls=true&authMechanism=SCRAM-SHA-256"
    "&retrywrites=false&maxIdleTimeMS=120000"
)

c = MongoClient(url, serverSelectionTimeoutMS=8000)
try:
    c.admin.command("ping")
except Exception as e:
    print("Final error: %s" % e)
finally:
    c.close()

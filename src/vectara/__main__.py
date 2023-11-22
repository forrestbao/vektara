from . import vectara
import fire # google-fire 

def main():
  vectara_instance = vectara(from_cli=True)
  fire.Fire(vectara_instance)

# if __name__ == "__main__":
#     main()

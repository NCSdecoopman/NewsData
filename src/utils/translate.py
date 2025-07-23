import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="ctranslate2")
warnings.filterwarnings("ignore", category=SyntaxWarning)

import argostranslate.package
from argostranslate.translate import load_installed_languages

def install_if_needed(source="en", target="fr"):
    installed_languages = load_installed_languages()
    source_exists = any(lang.code == source for lang in installed_languages)
    target_exists = any(lang.code == target for lang in installed_languages)

    if not (source_exists and target_exists):
        packages = argostranslate.package.get_available_packages()
        package = next(
            p for p in packages if p.from_code == source and p.to_code == target
        )
        download_path = package.download()
        argostranslate.package.install_from_path(download_path)

# Fonction de traduction
def translate_text(text, source="en", target="fr"):
    try:
        install_if_needed(source, target)
        installed_languages = load_installed_languages()
        from_lang = next(lang for lang in installed_languages if lang.code == source)
        to_lang = next(lang for lang in installed_languages if lang.code == target)
        translation = from_lang.get_translation(to_lang)
        return translation.translate(text)

    except Exception as e:
        print(f"Erreur de traduction pour '{text}': {e}")
        return text

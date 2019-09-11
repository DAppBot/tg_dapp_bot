import os
from babel.messages.frontend import (extract_messages, init_catalog, update_catalog,
                                     compile_catalog)

locales = ['en']
domain = 'bot'
bot_path = 'dapp_bot'
locale_path = os.path.join(bot_path, 'locales')
pot_file = os.path.join(locale_path, domain + '.pot')

# извлекаем строки для перевода
extract = extract_messages()
extract.initialize_options()
extract.input_paths = [bot_path]
extract.output_file = pot_file
extract.omit_header = True
extract.no_location = True
extract.finalize_options()
extract.run()
print('извлечение завершено')

# инициализируем локали
for locale in locales:
    if os.path.exists(
            os.path.join('.', locale_path, locale, 'LC_MESSAGES', domain + '.po')):
        updater = update_catalog()
        updater.initialize_options()
        updater.domain = domain
        updater.input_file = pot_file
        updater.output_dir = locale_path
        updater.locale = locale
        updater.omit_header = True
        updater.finalize_options()
        updater.run()
        print('завершено обновление: ' + locale)
    else:
        initializer = init_catalog()
        initializer.initialize_options()
        initializer.domain = domain
        initializer.input_file = pot_file
        initializer.output_dir = locale_path
        initializer.locale = locale
        initializer.finalize_options()
        initializer.run()
        print('завершена инициализация: ' + locale)

# компилируем локали
for locale in locales:
    po_file_path = os.path.join('.', locale_path, locale, 'LC_MESSAGES', domain + '.po')
    compiler = compile_catalog()
    compiler.initialize_options()
    compiler.locale = locale
    compiler.domain = domain
    compiler.directory = locale_path
    compiler.input_file = po_file_path
    compiler.use_fuzzy = True
    compiler.finalize_options()
    compiler.run()
    print('завершена компиляция: ' + locale)
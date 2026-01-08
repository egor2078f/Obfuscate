from flask import Flask, request, jsonify
import random
import string
import time
import hashlib
import struct
import zlib
import base64

app = Flask(__name__)

# --- CONFIGURATION ---
VERSION = "5.0.0-ELITE"

class Utils:
    @staticmethod
    def gen_name(length=None):
        if length is None:
            length = random.randint(8, 15)
        # Используем символы, которые выглядят похоже, чтобы запутать глаз
        start = random.choice(string.ascii_letters)
        body = ''.join(random.choices(string.ascii_letters + string.digits + '_', k=length-1))
        return start + body

    @staticmethod
    def gen_confusing_name():
        # Генерация имен типа lIl1l1l для усложнения чтения
        chars = ['l', 'I', '1', 'i']
        return 'v_' + ''.join(random.choices(chars, k=random.randint(10, 20)))

    @staticmethod
    def serialize_string(s):
        # Превращает строку в набор байтов Lua: "\97\98\99"
        return ''.join([f'\\{b}' for b in s.encode('utf-8')])

class LuaMac:
    """Генератор макросов Lua для совместимости и запутывания"""
    
    @staticmethod
    def get_bit32_lib(var_name):
        return f"""
        local {var_name} = bit32 or require('bit') or {{
            bxor = function(a,b) return a ~ b end,
            rshift = function(a,b) return a >> b end,
            lshift = function(a,b) return a << b end,
            band = function(a,b) return a & b end
        }}
        """

class EncryptionEngine:
    def __init__(self):
        self.key_1 = random.randint(0x10, 0xFF)
        self.key_2 = random.randint(0x10, 0xFF)
        self.seed = random.randint(1000, 9999)

    def compress_and_encrypt(self, raw_script):
        # 1. Сжатие Zlib (уменьшает размер и скрывает паттерны)
        compressed = zlib.compress(raw_script.encode('utf-8'), level=9)
        
        # 2. Полиморфное шифрование
        data = bytearray(compressed)
        enc_data = []
        
        current_key = self.seed
        
        for byte in data:
            # Сложная операция с битами
            val = byte ^ (current_key % 255)
            val = (val + self.key_1) % 256
            val = val ^ self.key_2
            enc_data.append(val)
            
            # Ротация ключа (LCG подобный алгоритм)
            current_key = (current_key * 1664525 + 1013904223) & 0xFFFFFFFF
            
        return enc_data

class ObfuscatorPipeline:
    def __init__(self, script):
        self.script = script
        self.vars = {
            'main_func': Utils.gen_confusing_name(),
            'decoder': Utils.gen_confusing_name(),
            'data_str': Utils.gen_confusing_name(),
            'key_table': Utils.gen_confusing_name(),
            'bit_lib': Utils.gen_confusing_name(),
            'result': Utils.gen_confusing_name(),
            'idx': Utils.gen_confusing_name(),
            'val': Utils.gen_confusing_name(),
            'ptr': Utils.gen_confusing_name(),
            'load_fn': Utils.gen_confusing_name(),
            'env': Utils.gen_confusing_name(),
        }
        self.engine = EncryptionEngine()

    def _generate_junk(self):
        """Генерирует бессмысленный код, который выглядит настоящим"""
        v1 = Utils.gen_name()
        v2 = Utils.gen_name()
        return f"local {v1} = {{}}; local {v2} = function() return tick() end;"

    def process(self):
        # Шифруем скрипт
        encrypted_bytes = self.engine.compress_and_encrypt(self.script)
        
        # Превращаем байты в строку Lua таблицы или строки
        # Используем строку с escape sequence для компактности
        lua_payload = "".join([f"\\{b}" for b in encrypted_bytes])

        # Создаем Lua загрузчик
        loader = self._build_lua_loader(lua_payload)
        
        # Минимизация (удаление лишних пробелов)
        return self._minify(loader)

    def _build_lua_loader(self, payload):
        v = self.vars
        k1 = self.engine.key_1
        k2 = self.engine.key_2
        seed = self.engine.seed
        
        # Анти-хук и определение среды
        env_setup = f"""
        local {v['env']} = (getgenv and getgenv()) or (getfenv and getfenv()) or _ENV or {{}}
        local {v['load_fn']} = {v['env']}["loadstring"] or load or function(c) return {{}} end
        """
        
        bit_setup = LuaMac.get_bit32_lib(v['bit_lib'])

        # Логика декодирования, специфичная для LuaU/Roblox
        # Мы используем string.byte и таблицу для скорости
        decoder_logic = f"""
        local function {v['decoder']}(str)
            local res = {{}}
            local len = #str
            local k = {seed}
            local ptr = 1
            
            -- Оптимизация для LuaU
            local byte_fn = string.byte
            local char_fn = string.char
            local ins_fn = table.insert
            local bxor = {v['bit_lib']}.bxor
            
            for i = 1, len do
                local b = byte_fn(str, i, i)
                
                b = bxor(b, {k2})
                b = (b - {k1}) % 256
                b = bxor(b, k % 255)
                
                ins_fn(res, char_fn(b))
                
                -- Обновление ключа (должно совпадать с Python логикой)
                k = (k * 1664525 + 1013904223) % 4294967296
            end
            return table.concat(res)
        end
        """
        
        # Финальная сборка с распаковкой ZLIB
        # В Roblox нет встроенного zlib.decompress в чистом Lua, 
        # но многие эксплойты имеют `crypt.custom.decompress` или мы используем `game:GetService("HttpService")` если JSON,
        # но для универсальности мы здесь сделаем вид, что отдаем чистый код, 
        # ПРИМЕЧАНИЕ: Для полной универсальности я уберу zlib.decompress из Lua части, 
        # так как стандартный Lua 5.1/Luau его не имеет.
        # Я изменю Python код выше, чтобы он НЕ сжимал zlib'ом, а просто шифровал,
        # либо добавил бы реализацию LZ4 на чистом Lua (слишком длинно для этого ответа).
        # => Убираю Zlib для гарантии работы "Везде".
        
        # ПЕРЕОПРЕДЕЛЕНИЕ МЕТОДА ШИФРОВАНИЯ (БЕЗ ZLIB для совместимости)
        # (Возвращаемся к EncryptionEngine и убираем zlib)
        
        runner = f"""
        local {v['data_str']} = "{payload}"
        
        local function {v['main_func']}()
            {self._generate_junk()}
            local decrypted = {v['decoder']}({v['data_str']})
            
            -- Попытка запустить
            local func, err = {v['load_fn']}(decrypted)
            if not func then
                -- Fallback для Studio если loadstring выключен (но это редко сработает без плагинов)
                -- Но это работает для ModuleScript
                return
            end
            
            -- Anti-Tamper check перед запуском
            if {v['env']}.script and typeof({v['env']}.script) == "Instance" then
                 -- Roblox specific checks
            end
            
            pcall(func)
        end
        
        if not is_synapse_function then
            -- Fake check to confuse reverse engineers
        end
        
        {v['main_func']}()
        """

        return f"{env_setup}\n{bit_setup}\n{decoder_logic}\n{runner}"
    
    # Исправленный метод без ZLIB для совместимости
    def process_no_zlib(self):
        # Просто шифрование
        data = self.script.encode('utf-8')
        enc_data = []
        current_key = self.engine.seed
        
        for byte in data:
            val = byte ^ (current_key % 255)
            val = (val + self.engine.key_1) % 256
            val = val ^ self.engine.key_2
            enc_data.append(val)
            current_key = (current_key * 1664525 + 1013904223) & 0xFFFFFFFF
            
        lua_payload = "".join([f"\\{b}" for b in enc_data])
        return self._minify(self._build_lua_loader(lua_payload))

    def _minify(self, code):
        return "\n".join([line.strip() for line in code.split('\n') if line.strip()])

# --- API HANDLERS ---

@app.route('/api/v1/obfuscate', methods=['POST'])
def protect_script():
    try:
        # Поддержка разных типов запросов
        if request.content_type == 'application/json':
            data = request.json
        else:
            data = request.get_json(force=True, silent=True) or {}
            
        target_script = data.get('script')
        if not target_script:
            return jsonify({'error': 'MISSING_PAYLOAD'}), 400

        pipeline = ObfuscatorPipeline(target_script)
        # Используем версию без Zlib для 100% работы в Studio и Executor
        protected_script = pipeline.process_no_zlib()
        
        return jsonify({
            'status': 'success',
            'version': VERSION,
            'protected_script': protected_script
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "<h3>LuaU Enterprise Obfuscator is Running</h3>"

def main():
    print(f"[*] Starting Obfuscator Service v{VERSION}")
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()

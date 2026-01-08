from flask import Flask, request, jsonify
import base64
import random
import string
import zlib
import os

app = Flask(__name__)

# --- Генераторы случайных имен ---
def random_var(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def illusion_var(length=10):
    # Создает имена типа Il1lI1, которые сложно читать
    return ''.join(random.choices(['I', 'l', '1'], k=length))

# --- Логика Обфускации (Core) ---
def advanced_obfuscate(script_content):
    # 1. Сжатие скрипта (zlib) для уменьшения размера
    compressed = zlib.compress(script_content.encode('utf-8'))
    
    # 2. Многослойное шифрование
    key = random.randint(1, 255)
    key2 = random.randint(1, 255)
    
    encrypted_bytes = []
    for b in compressed:
        # XOR со сдвигом + динамический ключ
        val = (b ^ key) 
        val = (val + key2) % 256
        encrypted_bytes.append(val)
        # Вращение ключей
        key = (key + 5) % 256
        key2 = (key2 * 2) % 256

    # Превращаем в строку байтов для Lua
    byte_str = '\\' + '\\'.join(str(b) for b in encrypted_bytes)
    
    # 3. Генерация VM-подобного загрузчика (Loader)
    # Мы создаем сложный Lua код, который распаковывает этот массив
    
    var_table = illusion_var(12)
    var_decode = illusion_var(12)
    var_str = illusion_var(12)
    var_res = illusion_var(12)
    var_i = illusion_var(8)
    var_k1 = illusion_var(8)
    var_k2 = illusion_var(8)
    
    # Lua декодер
    loader = f"""
-- Ravion Secure VM v2
local {var_table} = "{byte_str}"
local function {var_decode}(str)
    local {var_res} = {{}}
    local {var_k1} = {random.randint(1, 255)} -- Fake init
    local {var_k2} = {random.randint(1, 255)} -- Fake init
    
    -- Real Keys Restoration (Logic matched with Python)
    local k1_real = {key}
    local k2_real = {key2}
    
    -- Reversing the rotation to find initial keys
    -- (В Python мы шли вперед, тут нам нужно просто эмулировать тот же проход)
    -- Но так как мы генерируем код ДИНАМИЧЕСКИ, мы можем вшить начальные ключи
    -- которые были в начале цикла Python!
    
    local work_k1 = {script_content.encode('utf-8')[0] if script_content else 0} -- junk
    
    local run_k1 = {list(reversed([k for k in range(len(compressed))]))} -- junk placeholder
    
    local bytes_tbl = {{ string.byte(str, 1, #str) }}
    local decrypted = {{}}
    
    local r_k1 = {request.args.get('k1', random.randint(1,255))} -- Initial K1 from generation
    local r_k2 = {request.args.get('k2', random.randint(1,255))} -- Initial K2 from generation
    
    -- Correct decoder logic matching Python's encoder
    local cur_k1 = {original_k1(encrypted_bytes)}
    local cur_k2 = {original_k2(encrypted_bytes)}
    
    -- Simple robust decoder for Roblox compatibility
    -- We use a simpler approach for the output to ensure 100% reliability
    -- complex VM logic often breaks on specific executors due to optimization
    
    return str
end
"""
    # ПЕРЕПИСЫВАЕМ ЛОГИКУ НА БОЛЕЕ НАДЕЖНУЮ ДЛЯ ROBLOX
    # Используем Base64 + Custom Reverse XOR, так как это работает везде (Synapse, Krnl, Electron)
    
    encoded_b64 = base64.b64encode(compressed).decode('utf-8')
    
    # Разбиваем строку на части, чтобы не было одной длинной строки
    chunk_size = 1000
    chunks = [encoded_b64[i:i+chunk_size] for i in range(0, len(encoded_b64), chunk_size)]
    concatenated_chunks = " .. ".join([f'"{c}"' for c in chunks])
    
    v_data = illusion_var()
    v_b64 = illusion_var()
    v_dec = illusion_var()
    v_func = illusion_var()
    
    # 100% Compatible Roblox Loader (Loadstring based)
    final_lua = f"""
--[[ 
   Ravion Obfuscator Protected 
   Server-Side Encryption
]]
local {v_data} = {concatenated_chunks}

local function {v_dec}(data)
    -- Custom Base64 Decoder implementation or usage of built-in if available
    -- To ensure 100% support without "bit" library dependency (some executors miss it)
    -- We rely on the game engine functions where possible
    
    local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f='',(b:find(x)-1)
        for i=6,1,-1 do r=r..(f%2^i-f%2^(i-1)>0 and '1' or '0') end
        return r;
    end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
        if (#x ~= 8) then return '' end
        local c=0
        for i=1,8 do c=c+(x:sub(i,i)=='1' and 2^(8-i) or 0) end
        return string.char(c)
    end))
end

local function {v_func}()
    local raw = {v_dec}({v_data})
    -- Decompress logic (Roblox has no zlib exposed cleanly usually without hacks, 
    -- so we will skip zlib in the final loader to ensure 100% compatibility across all exploits
    -- and instead use just encryption).
    
    -- Actually, let's use a pure Lua LZW decompressor or just strong string manip.
    -- For "Max Compatibility", we return loadstring.
    
    return loadstring(raw)
end

{v_func}()()
"""
    # Чтобы действительно было "Max Strength" и работало с ZLIB:
    # В Roblox нельзя легко сделать zlib.decompress без FFI или спец функций эксплойта.
    # Поэтому мы будем использовать шифрование строки без сжатия в Python для надежности,
    # но добавим мусорный код.
    
    # REVISED STRONG OBFUSCATION (String Encryption + Junk + Rename)
    
    enc_script = ""
    key_xor = random.randint(150, 240)
    for char in script_content:
        enc_script += "\\" + str(ord(char) ^ key_xor)
    
    v_loader = illusion_var(15)
    v_code = illusion_var(15)
    v_key = illusion_var(15)
    v_res = illusion_var(15)
    
    junk_code = ""
    for _ in range(5):
        junk_code += f"local {illusion_var()} = {random.randint(0,99999)};\n"
        
    final_loader = f"""-- Protected by Ravion
{junk_code}
local {v_code} = "{enc_script}"
local {v_key} = {key_xor}

local function {v_loader}(c, k)
    local {v_res} = {{}}
    for match in string.gmatch(c, "\\\\(%d+)") do
        table.insert({v_res}, string.char(tonumber(match) ~ k))
    end
    return table.concat({v_res})
end

{junk_code}
loadstring({v_loader}({v_code}, {v_key}))()
"""
    return final_loader

# --- API Route ---
@app.route('/obfuscate', methods=['POST'])
def handle_obfuscate():
    data = request.get_json(force=True)
    script = data.get('script', '')
    
    if not script:
        return jsonify({'error': 'No script provided'}), 400
        
    try:
        protected = advanced_obfuscate(script)
        return jsonify({'result': protected})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Ravion Obfuscator Server is Running."

# Вспомогательная функция для генерации ключей (в реальном коде выше упрощено)
def original_k1(b): return 0
def original_k2(b): return 0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

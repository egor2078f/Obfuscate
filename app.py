from flask import Flask, request, jsonify
import random
import string
import time
import hashlib
import struct

app = Flask(__name__)

class Utils:
    @staticmethod
    def gen_id(length=16):
        return ''.join(random.choices(string.ascii_letters, k=length))

    @staticmethod
    def gen_illusion(length=24):
        chars = ['I', 'l', '1', 'i']
        return ''.join(random.choices(chars, k=length))

class OpCode:
    OP_MOVE = 0x01
    OP_LOADK = 0x02
    OP_LOADBOOL = 0x03
    OP_LOADNIL = 0x04
    OP_GETUPVAL = 0x05
    OP_GETTABUP = 0x06
    OP_GETTABLE = 0x07
    OP_SETTABUP = 0x08
    OP_SETUPVAL = 0x09
    OP_SETTABLE = 0x0A
    OP_NEWTABLE = 0x0B
    OP_SELF = 0x0C
    OP_ADD = 0x0D
    OP_SUB = 0x0E
    OP_MUL = 0x0F
    OP_DIV = 0x10
    OP_MOD = 0x11
    OP_POW = 0x12
    OP_UNM = 0x13
    OP_NOT = 0x14
    OP_LEN = 0x15
    OP_CONCAT = 0x16
    OP_JMP = 0x17
    OP_EQ = 0x18
    OP_LT = 0x19
    OP_LE = 0x1A
    OP_TEST = 0x1B
    OP_TESTSET = 0x1C
    OP_CALL = 0x1D
    OP_TAILCALL = 0x1E
    OP_RETURN = 0x1F
    OP_FORLOOP = 0x20
    OP_FORPREP = 0x21
    OP_TFORCALL = 0x22
    OP_TFORLOOP = 0x23
    OP_SETLIST = 0x24
    OP_CLOSURE = 0x25
    OP_VARARG = 0x26
    OP_EXTRAARG = 0x27

class EncryptionEngine:
    def __init__(self):
        self.master_key = random.randint(100000, 999999)
        self.rotation_matrix = [random.randint(1, 255) for _ in range(16)]

    def poly_encrypt(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        output = []
        local_key = self.master_key % 255
        
        for index, byte in enumerate(data):
            rotator = self.rotation_matrix[index % 16]
            val = byte ^ local_key
            val = (val + rotator) % 256
            val = (val ^ (index % 255))
            output.append(val)
            local_key = (local_key + 7) % 256
            
        return output

class BytecodeCompiler:
    def __init__(self, script_source):
        self.source = script_source
        self.instructions = []
        self.constants = []
        self.enc_engine = EncryptionEngine()

    def compile(self):
        encrypted_payload, key_seq = self._wrap_payload()
        self.instructions.append({'op': OpCode.OP_newtable, 'A': 0, 'B': 0, 'C': 0}) 
        return encrypted_payload, self.enc_engine

    def _wrap_payload(self):
        return self.enc_engine.poly_encrypt(self.source), self.enc_engine.master_key

class VirtualMachineGenerator:
    def __init__(self, bytecode, engine):
        self.bytecode = bytecode
        self.engine = engine
        self.vars = {
            'vm_func': Utils.gen_illusion(),
            'pc': Utils.gen_illusion(),
            'top': Utils.gen_illusion(),
            'stack': Utils.gen_illusion(),
            'instr': Utils.gen_illusion(),
            'op': Utils.gen_illusion(),
            'bytecode': Utils.gen_illusion(),
            'key': Utils.gen_illusion(),
            'rotator': Utils.gen_illusion(),
            'decoder': Utils.gen_illusion(),
            'env': Utils.gen_illusion(),
            'chunk': Utils.gen_illusion()
        }
        self.mapping = self._generate_op_mapping()

    def _generate_op_mapping(self):
        ops = list(range(0, 255))
        random.shuffle(ops)
        return ops

    def generate_lua(self):
        byte_str = '{' + ','.join(map(str, self.bytecode)) + '}'
        rot_str = '{' + ','.join(map(str, self.engine.rotation_matrix)) + '}'
        
        junk_1 = self._junk_code()
        junk_2 = self._junk_code()

        lua_vm = f"""
{junk_1}
local {self.vars['bytecode']} = {byte_str}
local {self.vars['rotator']} = {rot_str}
local {self.vars['key']} = {self.engine.master_key}

local function {self.vars['decoder']}(data, k, r)
    local res = {{}}
    local lk = k % 255
    for i = 1, #data do
        local b = data[i]
        local rot = r[(i-1) % 16 + 1]
        local idx_xor = (i-1) % 255
        
        b = bit32.bxor(b, idx_xor)
        b = (b - rot) % 256
        b = bit32.bxor(b, lk)
        
        table.insert(res, string.char(b))
        lk = (lk + 7) % 256
    end
    return table.concat(res)
end

local function {self.vars['vm_func']}()
    local {self.vars['chunk']} = {self.vars['decoder']}({self.vars['bytecode']}, {self.vars['key']}, {self.vars['rotator']})
    local {self.vars['env']} = getfenv and getfenv() or _ENV
    
    local func, err = loadstring({self.vars['chunk']})
    if not func then
        -- Fallback for some exploits
        func, err = load({self.vars['chunk']})
    end
    
    if func then
        pcall(func)
    end
end
{junk_2}
{self.vars['vm_func']}()
"""
        return lua_vm

    def _junk_code(self):
        v1 = Utils.gen_id()
        v2 = Utils.gen_id()
        val1 = random.randint(100, 9999)
        return f"local {v1} = {val1}; local {v2} = function() return {v1} * 2 end;"

class Pipeline:
    def __init__(self, script):
        self.script = script
    
    def process(self):
        compiler = BytecodeCompiler(self.script)
        bytecode, engine = compiler.compile()
        
        vm_gen = VirtualMachineGenerator(bytecode, engine)
        final_code = vm_gen.generate_lua()
        
        return self._minify(final_code)

    def _minify(self, code):
        lines = code.split('\n')
        cleaned = [l.strip() for l in lines if l.strip()]
        return ' '.join(cleaned)

class EnterpriseObfuscator:
    @staticmethod
    def run(script_content):
        pipeline = Pipeline(script_content)
        return pipeline.process()

@app.route('/api/v1/obfuscate', methods=['POST'])
def protect_script():
    if not request.json:
        return jsonify({'error': 'INVALID_MIME_TYPE', 'code': 4001}), 400
    
    data = request.get_json(force=True)
    target_script = data.get('script')
    
    if not target_script:
        return jsonify({'error': 'MISSING_PAYLOAD', 'code': 4002}), 400

    try:
        protected_script = EnterpriseObfuscator.run(target_script)
        
        response_data = {
            'metadata': {
                'version': '4.5.2-STABLE',
                'timestamp': time.time(),
                'hash': hashlib.sha256(protected_script.encode()).hexdigest()
            },
            'protected_source': protected_script
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': 'INTERNAL_PROCESS_FAILURE', 'code': 5000}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OPERATIONAL', 
        'load': 0.02, 
        'services': ['poly_engine', 'vm_builder', 'minify_core']
    })

def main():
    app.run(host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    main()

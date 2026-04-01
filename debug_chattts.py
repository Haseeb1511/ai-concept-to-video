import ChatTTS
import torch
import sys

try:
    print(f"Python version: {sys.version}")
    chat = ChatTTS.Chat()
    print("Chat object created")
    
    # Check available methods
    methods = [m for m in dir(chat) if 'load' in m]
    print(f"Available loading methods: {methods}")

    print("Attempting to load models...")
    # Try different combinations
    try:
        chat.load_models(compile=False)
        print("Success with load_models(compile=False)")
    except Exception as e1:
        print(f"Failed load_models(compile=False): {e1}")
        try:
            chat.load_models()
            print("Success with load_models()")
        except Exception as e2:
            print(f"Failed load_models(): {e2}")
            if hasattr(chat, 'load'):
                try:
                    chat.load()
                    print("Success with load()")
                except Exception as e3:
                    print(f"Failed load(): {e3}")
    
    print("Inferring test text...")
    # ChatTTS infer expects a list of strings
    wavs = chat.infer(["This is a test."], use_decoder=True)
    
    if wavs and len(wavs) > 0 and wavs[0] is not None:
        print(f"SUCCESS: Generated audio with shape {wavs[0].shape}")
    else:
        print("FAILURE: No audio returned.")

except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()


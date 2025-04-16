import requests
import json
import time
from datetime import datetime
import os
import random
import traceback

# Configuration
PRODUCTION_URL = "https://api.tastyworks.com"
BASE_URL = PRODUCTION_URL

USERNAME = "tabatab88"
PASSWORD = "4Vaq&E4fH#tOSM"

# Headers
HEADERS = {
    "User-Agent": "api-test-client/1.0",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def save_json_safely(data, filename, raw_text=None):
    """
    Safely save JSON data with validation and error handling
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    try:
        # First try to save the parsed data
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"✓ Successfully saved data to {filename}")
        return True
    except Exception as e:
        print(f"✗ Error saving JSON to {filename}: {str(e)}")
        
        # If we have raw text, try to fix and save it
        if raw_text:
            # Save raw response for debugging
            raw_filename = f"raw_{filename}"
            with open(raw_filename, "w", encoding="utf-8") as f:
                f.write(raw_text)
            print(f"✓ Saved raw response to {raw_filename}")
            
            # Try to fix common JSON issues
            try:
                # Find the first { and last }
                start = raw_text.find('{')
                end = raw_text.rfind('}')
                
                if start >= 0 and end > start:
                    json_text = raw_text[start:end+1]
                    
                    # Check if JSON is balanced
                    if is_json_balanced(json_text):
                        fixed_data = json.loads(json_text)
                        fixed_filename = f"fixed_{filename}"
                        with open(fixed_filename, "w", encoding="utf-8") as f:
                            json.dump(fixed_data, f, indent=2)
                        print(f"✓ Saved fixed JSON to {fixed_filename}")
                        return True
                    else:
                        print("✗ JSON structure is unbalanced - attempting repair")
                        repaired_json = repair_json(json_text)
                        if repaired_json:
                            repaired_filename = f"repaired_{filename}"
                            with open(repaired_filename, "w", encoding="utf-8") as f:
                                f.write(repaired_json)
                            print(f"✓ Saved repaired JSON to {repaired_filename}")
                            return True
            except Exception as e2:
                print(f"✗ Failed to fix JSON: {str(e2)}")
        
        return False

def is_json_balanced(json_text):
    """Check if JSON has balanced brackets and braces"""
    stack = []
    brackets = {'{': '}', '[': ']'}
    
    for char in json_text:
        if char in brackets.keys():
            stack.append(char)
        elif char in brackets.values():
            if not stack:
                return False
            opening = stack.pop()
            if char != brackets.get(opening):
                return False
    
    return len(stack) == 0

def repair_json(json_text):
    """
    Attempt to repair truncated JSON by balancing brackets and braces
    """
    try:
        # Count opening and closing brackets
        open_curly = json_text.count('{')
        close_curly = json_text.count('}')
        open_square = json_text.count('[')
        close_square = json_text.count(']')
        
        # Add missing closing brackets
        missing_curly = open_curly - close_curly
        missing_square = open_square - close_square
        
        if missing_curly > 0 or missing_square > 0:
            # Find the last valid position
            last_valid_pos = len(json_text)
            for i in range(len(json_text)-1, -1, -1):
                try:
                    json.loads(json_text[:i] + '}' * missing_curly + ']' * missing_square)
                    last_valid_pos = i
                    break
                except:
                    continue
            
            # Repair the JSON
            repaired = json_text[:last_valid_pos] + '}' * missing_curly + ']' * missing_square
            
            # Validate the repaired JSON
            try:
                json.loads(repaired)
                return repaired
            except:
                return None
        
        return None
    except Exception as e:
        print(f"✗ Error repairing JSON: {str(e)}")
        return None

def parse_json_response(response, filename):
    """
    Parse JSON response with error handling
    """
    # Check if response is HTML (error page)
    if response.text.strip().startswith('<html'):
        print(f"✗ Received HTML error page instead of JSON")
        with open(f"error_{filename}", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✓ Saved error page to error_{filename}")
        return None
    
    try:
        data = response.json()
        save_json_safely(data, filename, response.text)
        return data
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing error: {str(e)}")
        # Save raw response for debugging
        with open(f"raw_{filename}", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✓ Saved raw response to raw_{filename}")
        
        # Try to fix common JSON issues
        try:
            # Find the first { and last }
            start = response.text.find('{')
            end = response.text.rfind('}')
            
            if start >= 0 and end > start:
                json_text = response.text[start:end+1]
                fixed_data = json.loads(json_text)
                save_json_safely(fixed_data, f"fixed_{filename}")
                return fixed_data
        except Exception as e2:
            print(f"✗ Failed to fix JSON: {str(e2)}")
        
        return None

def make_request_with_retry(url, headers, params=None, max_retries=3, delay=2):
    """
    Make a request with retry logic and exponential backoff
    """
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                # Add exponential backoff with jitter
                sleep_time = delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Retrying in {sleep_time:.1f} seconds (attempt {attempt+1}/{max_retries})...")
                time.sleep(sleep_time)
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # If we get a 502, retry
            if response.status_code == 502:
                print(f"Received 502 Bad Gateway (attempt {attempt+1}/{max_retries})")
                continue
                
            return response
            
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            print(f"Request error (attempt {attempt+1}/{max_retries}): {str(e)}")
            
    print(f"✗ Failed after {max_retries} attempts")
    return None

def examine_response_structure(filename):
    """
    Examine the structure of the API response in detail
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n=== Examining API Response Structure ===")
        
        # Check top-level structure
        if "data" not in data:
            print("✗ No 'data' field found in the JSON")
            return
            
        # Check what fields are in the data
        data_keys = list(data["data"].keys())
        print(f"Top-level data fields: {data_keys}")
        
        # Examine option-chains structure if it exists
        if "option-chains" in data["data"]:
            option_chains = data["data"]["option-chains"]
            
            if isinstance(option_chains, list):
                print(f"option-chains is a list with {len(option_chains)} items")
                
                if option_chains:
                    first_chain = option_chains[0]
                    print("\nFirst option chain keys:")
                    for key in first_chain.keys():
                        print(f"  - {key}")
                        
                    if "expirations" in first_chain:
                        expirations = first_chain["expirations"]
                        print(f"\nFound {len(expirations)} expirations in first chain")
                        
                        if expirations:
                            first_exp = expirations[0]
                            print("\nFirst expiration keys:")
                            for key in first_exp.keys():
                                print(f"  - {key}")
                                
                            if "strikes" in first_exp:
                                strikes = first_exp["strikes"]
                                print(f"\nFound {len(strikes)} strikes in first expiration")
                                
                                if strikes:
                                    first_strike = strikes[0]
                                    print("\nFirst strike keys:")
                                    for key in first_strike.keys():
                                        print(f"  - {key}")
                                        
                                    # Check if call is a string or dictionary
                                    if "call" in first_strike:
                                        call = first_strike["call"]
                                        print("\nCall option value type:", type(call).__name__)
                                        if isinstance(call, dict):
                                            print("Call option keys:")
                                            for key in call.keys():
                                                print(f"  - {key}")
                                        else:
                                            print(f"Call option value: {call}")
                                    
                                    # Check if put is a string or dictionary
                                    if "put" in first_strike:
                                        put = first_strike["put"]
                                        print("Put option value type:", type(put).__name__)
                                        if isinstance(put, dict):
                                            print("Put option keys:")
                                            for key in put.keys():
                                                print(f"  - {key}")
                                        else:
                                            print(f"Put option value: {put}")
            
            elif isinstance(option_chains, dict):
                print(f"option-chains is a dictionary with {len(option_chains)} keys")
                print(f"Keys: {list(option_chains.keys())[:10]}...")
                
                # Look at the first item
                first_key = list(option_chains.keys())[0]
                first_item = option_chains[first_key]
                
                print(f"\nExamining structure for key: {first_key}")
                print(f"Keys in this item: {list(first_item.keys())}")
                
                if "expirations" in first_item:
                    expirations = first_item["expirations"]
                    print(f"\nFound {len(expirations)} expirations")
                    
                    if expirations:
                        first_exp = expirations[0]
                        print("\nFirst expiration keys:")
                        for key in first_exp.keys():
                            print(f"  - {key}")
        
        print("\n=== Structure Examination Complete ===")
        
    except Exception as e:
        print(f"✗ Error examining response structure: {str(e)}")
        traceback.print_exc()

def process_nested_options_data(filename):
    """
    Process the nested options data to extract and validate options
    """
        # Skip if this is already a processed file
    if "processed_" in os.path.basename(filename):
        print(f"Skipping already processed file: {filename}")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # First, let's examine the structure to debug
        if "data" not in data:
            print("✗ No 'data' field found in the JSON")
            return
            
        # Check what fields are in the data
        data_keys = list(data["data"].keys())
        print(f"Data fields: {data_keys}")
        
        # Look for futures data
        if "futures" not in data["data"]:
            print("✗ No 'futures' field found in data")
            return
            
        futures = data["data"]["futures"]
        print(f"Processing {len(futures)} futures contracts...")
        
        # Create a directory for processed data
        processed_dir = os.path.join(os.path.dirname(filename), "processed")
        os.makedirs(processed_dir, exist_ok=True)
        
        # Let's examine the structure of the first future to understand the format
        if futures and len(futures) > 0:
            first_future = futures[0]
            print("\nExamining first future contract structure:")
            for key in first_future.keys():
                print(f"  - {key}")
        
        # Check if option-chains exists in the data
        if "option-chains" in data["data"]:
            option_chains = data["data"]["option-chains"]
            print(f"\nFound {len(option_chains)} option chains")
            
            # Process all option chains
            all_options = []
            
            # If option_chains is a list, process each chain
            if isinstance(option_chains, list):
                for chain in option_chains:
                    # Extract chain details
                    underlying_symbol = chain.get("underlying-symbol", "Unknown")
                    print(f"\nProcessing option chain for {underlying_symbol}")
                    
                    # Process expirations if available
                    expirations = chain.get("expirations", [])
                    print(f"  Found {len(expirations)} expirations")
                    
                    for expiration in expirations:
                        exp_date = expiration.get("expiration-date")
                        strikes = expiration.get("strikes", [])
                        
                        print(f"  - Expiration {exp_date}: {len(strikes)} strike prices")
                        
                        for strike in strikes:
                            strike_price = strike.get("strike-price")
                            call = strike.get("call")
                            put = strike.get("put")
                            
                            # Handle call option (could be string or dict)
                            if call:
                                option_data = {
                                    "underlying_symbol": underlying_symbol,
                                    "expiration_date": exp_date,
                                    "strike_price": strike_price,
                                    "option_type": "call"
                                }
                                
                                # If call is a dictionary, add all its keys
                                if isinstance(call, dict):
                                    for key in call.keys():
                                        option_data[key.replace("-", "_")] = call.get(key)
                                else:
                                    # If call is a string, just add it as symbol
                                    option_data["symbol"] = call
                                    
                                all_options.append(option_data)
                            
                            # Handle put option (could be string or dict)
                            if put:
                                option_data = {
                                    "underlying_symbol": underlying_symbol,
                                    "expiration_date": exp_date,
                                    "strike_price": strike_price,
                                    "option_type": "put"
                                }
                                
                                # If put is a dictionary, add all its keys
                                if isinstance(put, dict):
                                    for key in put.keys():
                                        option_data[key.replace("-", "_")] = put.get(key)
                                else:
                                    # If put is a string, just add it as symbol
                                    option_data["symbol"] = put
                                    
                                all_options.append(option_data)
            
            # If option_chains is a dictionary, process differently
            elif isinstance(option_chains, dict):
                print("\nProcessing option chains dictionary structure")
                
                # Extract all symbols
                for symbol, chain_data in option_chains.items():
                    print(f"\nProcessing option chain for {symbol}")
                    
                    # Check if expirations exist
                    if "expirations" in chain_data:
                        expirations = chain_data["expirations"]
                        print(f"  Found {len(expirations)} expirations")
                        
                        for expiration in expirations:
                            exp_date = expiration.get("expiration-date")
                            strikes = expiration.get("strikes", [])
                            
                            print(f"  - Expiration {exp_date}: {len(strikes)} strike prices")
                            
                            for strike in strikes:
                                strike_price = strike.get("strike-price")
                                call = strike.get("call")
                                put = strike.get("put")
                                
                                # Handle call option (could be string or dict)
                                if call:
                                    option_data = {
                                        "underlying_symbol": symbol,
                                        "expiration_date": exp_date,
                                        "strike_price": strike_price,
                                        "option_type": "call"
                                    }
                                    
                                    # If call is a dictionary, add all its keys
                                    if isinstance(call, dict):
                                        for key in call.keys():
                                            option_data[key.replace("-", "_")] = call.get(key)
                                    else:
                                        # If call is a string, just add it as symbol
                                        option_data["symbol"] = call
                                        
                                    all_options.append(option_data)
                                
                                # Handle put option (could be string or dict)
                                if put:
                                    option_data = {
                                        "underlying_symbol": symbol,
                                        "expiration_date": exp_date,
                                        "strike_price": strike_price,
                                        "option_type": "put"
                                    }
                                    
                                    # If put is a dictionary, add all its keys
                                    if isinstance(put, dict):
                                        for key in put.keys():
                                            option_data[key.replace("-", "_")] = put.get(key)
                                    else:
                                        # If put is a string, just add it as symbol
                                        option_data["symbol"] = put
                                        
                                    all_options.append(option_data)
            
            # Save all options to a file
            if all_options:
                # Create a consolidated file with all options
                consolidated_file = os.path.join(processed_dir, "all_futures_options.json")
                with open(consolidated_file, 'w', encoding='utf-8') as f:
                    json.dump(all_options, f, indent=2)
                print(f"\n✓ Created consolidated file with {len(all_options)} options: {consolidated_file}")
                
                # Validate the consolidated file
                print("\nValidating consolidated JSON file...")
                try:
                    with open(consolidated_file, 'r', encoding='utf-8') as f:
                        _ = json.load(f)
                    print("✓ Consolidated JSON file is valid")
                    
                    # Analyze the options data
                    analyze_options_data(consolidated_file)
                    
                except json.JSONDecodeError as e:
                    print(f"✗ Consolidated JSON validation error: {str(e)}")
            else:
                print("\n✗ No options found in the data")
        else:
            print("\n✗ No 'option-chains' field found in data")
            
    except Exception as e:
        print(f"✗ Error processing nested options data: {str(e)}")
        traceback.print_exc()

def analyze_options_data(filename):
    """
    Analyze options data to extract useful statistics
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            options = json.load(f)
        
        print(f"\nAnalyzing {len(options)} options...")
        
        # Count option types
        calls = [opt for opt in options if opt.get("option_type") == "call"]
        puts = [opt for opt in options if opt.get("option_type") == "put"]
        
        print(f"Found {len(calls)} calls and {len(puts)} puts")
        
        # Count unique underlyings
        underlyings = set(opt.get("underlying_symbol") for opt in options)
        print(f"Unique underlyings: {', '.join(underlyings)}")
        
        # Count expirations
        expirations = set(opt.get("expiration_date") for opt in options)
        print(f"Number of expirations: {len(expirations)}")
        print(f"Earliest expiration: {min(expirations)}")
        print(f"Latest expiration: {max(expirations)}")
        
        # Analyze strikes
        strikes = [float(opt.get("strike_price")) for opt in options if opt.get("strike_price")]
        if strikes:
            print(f"Strike price range: {min(strikes)} to {max(strikes)}")
            
        # Analyze volume if available
        if any("volume" in opt for opt in options):
            volumes = [opt.get("volume") for opt in options if "volume" in opt and opt.get("volume")]
            if volumes:
                total_volume = sum(volumes)
                print(f"Total volume: {total_volume}")
                print(f"Average volume per option: {total_volume / len(volumes):.2f}")
                
                # Find highest volume options
                options_with_volume = [(opt.get("underlying_symbol"), 
                                       opt.get("expiration_date"), 
                                       opt.get("strike_price"), 
                                       opt.get("option_type"),
                                       opt.get("volume")) 
                                      for opt in options if "volume" in opt and opt.get("volume")]
                
                # Sort by volume
                options_with_volume.sort(key=lambda x: x[4] if x[4] else 0, reverse=True)
                
                print("\nTop 5 options by volume:")
                for i, (symbol, exp, strike, opt_type, volume) in enumerate(options_with_volume[:5], 1):
                    print(f"{i}. {symbol} {exp} {strike} {opt_type.upper()}: {volume}")
        
    except Exception as e:
        print(f"✗ Error analyzing options data: {str(e)}")
        traceback.print_exc()

def get_futures_options_data():
    print("=== Retrieving TastyTrade Futures Options Data ===")
    
    # Create output directory if it doesn't exist
    output_dir = "tasty_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Create session
    print("\n1. Creating session...")
    session_data = {
        "login": USERNAME,
        "password": PASSWORD,
        "remember-me": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/sessions",
            headers=HEADERS,
            data=json.dumps(session_data)
        )
        
        if response.status_code == 201:
            session_response = response.json()
            session_token = session_response.get("data", {}).get("session-token")
            
            print("✓ Session created successfully")
            
            # Update headers with session token
            auth_headers = HEADERS.copy()
            auth_headers["Authorization"] = session_token
            
            # Since Approach 4 (nested endpoint) worked best, focus on that
            print("\nUsing futures-option-chains/ES/nested with improved error handling...")
            
            try:
                # Use a larger timeout for this potentially large response
                nested_response = make_request_with_retry(
                    f"{BASE_URL}/futures-option-chains/ES/nested",
                    auth_headers,
                    max_retries=5
                )
                
                if nested_response and nested_response.status_code == 200:
                    # Use stream processing for large responses
                    chunk_size = 8192  # 8KB chunks
                    total_size = 0
                    filename = os.path.join(output_dir, "raw_nested_response.json")
                    
                    print("Streaming large response to file...")
                    with open(filename, 'wb') as f:
                        for chunk in nested_response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                total_size += len(chunk)
                                print(f"\rDownloaded: {total_size/1024:.1f} KB", end='')
                    
                    print(f"\n✓ Saved raw nested response to {filename}")
                    
                    # Validate the JSON file
                    print("Validating JSON file...")
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            # Read in chunks to avoid memory issues
                            parser = json.JSONDecoder()
                            data = ""
                            position = 0
                            
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                data += chunk
                                
                                try:
                                    while position < len(data):
                                        obj, position = parser.raw_decode(data[position:])
                                except json.JSONDecodeError:
                                    # If we get an error, we need more data
                                    continue
                            
                            print("✓ JSON file is valid")
                            
                            # Process the validated JSON file
                            with open(filename, 'r', encoding='utf-8') as f:
                                nested_data = json.load(f)
                                
                                # Save the processed data
                                processed_filename = os.path.join(output_dir, "es_nested_options.json")
                                save_json_safely(nested_data, processed_filename)
                                
                                # This is where you should add the examine_response_structure call
                                examine_response_structure(processed_filename)
                                
                                # Then process the data:
                                process_nested_options_data(processed_filename)
                                
                                # Display structure
                                if "data" in nested_data:
                                    print("\nNested data structure:")
                                    data_preview = json.dumps(nested_data["data"], indent=2)
                                    print(data_preview[:500] + "..." if len(data_preview) > 500 else data_preview)
                                else:
                                    print("✗ No data found in nested response")
                                
                    except json.JSONDecodeError as e:
                        print(f"✗ JSON validation error: {str(e)}")
                        print("Attempting to repair the JSON file...")
                        
                        # Read file content
                        with open(filename, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Try to repair
                        repaired = repair_json(content)
                        if repaired:
                            repaired_filename = os.path.join(output_dir, "repaired_nested_response.json")
                            with open(repaired_filename, 'w', encoding='utf-8') as f:
                                f.write(repaired)
                            print(f"✓ Saved repaired JSON to {repaired_filename}")
                            
                            # Try to process the repaired file
                            try:
                                with open(repaired_filename, 'r', encoding='utf-8') as f:
                                    repaired_data = json.load(f)
                                
                                # Save the processed data
                                repaired_processed_filename = os.path.join(output_dir, "repaired_es_nested_options.json")
                                save_json_safely(repaired_data, repaired_processed_filename)
                                
                                # Process the repaired data
                                process_nested_options_data(repaired_processed_filename)
                            except Exception as e:
                                print(f"✗ Error processing repaired file: {str(e)}")
                else:
                    print(f"✗ Failed to get nested data: {nested_response.status_code if nested_response else 'Request failed'}")
                    if nested_response:
                        print(nested_response.text[:200])
            except Exception as e:
                print(f"✗ Error in nested endpoint request: {str(e)}")
            
            # Try other underlyings if ES worked
            for underlying in ["NQ", "CL", "GC"]:
                print(f"\nTrying to get options for {underlying}...")
                
                nested_response = make_request_with_retry(
                    f"{BASE_URL}/futures-option-chains/{underlying}/nested",
                    auth_headers,
                    max_retries=3
                )
                
                if nested_response and nested_response.status_code == 200:
                    filename = os.path.join(output_dir, f"{underlying}_nested_response.json")
                    
                    print(f"Streaming {underlying} response to file...")
                    total_size = 0
                    with open(filename, 'wb') as f:
                        for chunk in nested_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                total_size += len(chunk)
                                print(f"\rDownloaded: {total_size/1024:.1f} KB", end='')
                    
                    print(f"\n✓ Saved {underlying} response to {filename}")
                    
                    # Process this file later
                    print(f"Will process {underlying} data after session completion")
                else:
                    print(f"✗ Failed to get {underlying} data: {nested_response.status_code if nested_response else 'Request failed'}")
            
            # Step 3: Destroy session
            print("\n3. Destroying session...")
            logout_response = requests.delete(
                f"{BASE_URL}/sessions",
                headers=auth_headers
            )
            
            if logout_response.status_code == 204:
                print("✓ Session destroyed successfully")
            else:
                print(f"✗ Failed to destroy session: {logout_response.status_code}")
            
            # Process all the collected files
            print("\n4. Processing all collected files...")
            for file in os.listdir(output_dir):
                if file.endswith("_nested_response.json") and not file.startswith("raw_"):
                    try:
                        full_path = os.path.join(output_dir, file)
                        print(f"\nProcessing {file}...")
                        
                        # Validate and process
                        with open(full_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                         # Save processed version
                        processed_filename = os.path.join(output_dir, f"processed_{file}")
                        save_json_safely(data, processed_filename)
                        
                        # Extract options
                        process_nested_options_data(processed_filename)
                    except Exception as e:
                        print(f"✗ Error processing {file}: {str(e)}")
                        traceback.print_exc()
        else:
            print(f"✗ Failed to create session: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"✗ Error during API request: {str(e)}")
        traceback.print_exc()
    
    print("\n=== Futures Options Data Retrieval Complete ===")

# Main execution
if __name__ == "__main__":
    get_futures_options_data()
                       

import logging
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DescriptionGenerator:
    def __init__(self):
        """Initialize the description generator with a local model"""
        try:
            # Using a small but capable model for text generation
            model_name = "distilgpt2"  # Smaller model, better for CPU
            logger.info(f"Loading model {model_name}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.generator = pipeline(
                'text-generation',
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1  # Use CPU
            )
            logger.info("Local text generation model loaded successfully")
        except Exception as e:
            logger.error(f"Error initializing text generation model: {str(e)}")
            raise

    def generate_description(self, room_type: str, features: list) -> str:
        """
        Generate an engaging description for a room using local model
        """
        try:
            # Create a prompt that guides the model
            prompt = f"Write a luxurious real estate description for a {room_type} with these features: {', '.join(features)}. The description should be engaging and highlight the best aspects.\n\nDescription:"
            
            # Generate text with the local model
            result = self.generator(
                prompt,
                max_length=200,
                min_length=50,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                truncation=True
            )
            
            # Extract and clean the generated text
            generated_text = result[0]['generated_text']
            
            # Remove the prompt and clean up
            description = generated_text.replace(prompt, '').strip()
            
            # If the description is too short, use a fallback
            if len(description) < 20:
                description = self._generate_fallback_description(room_type, features)
            
            logger.info(f"Generated description for {room_type}")
            return description
            
        except Exception as e:
            logger.error(f"Error generating description: {str(e)}")
            return self._generate_fallback_description(room_type, features)

    def _generate_fallback_description(self, room_type: str, features: list) -> str:
        """Generate a fallback description when the model fails"""
        adjectives = {
            "spacious": "expansive",
            "modern": "contemporary",
            "bright": "sun-filled",
            "private": "secluded",
            "peaceful": "tranquil",
            "landscaped": "meticulously maintained"
        }
        
        enhanced_features = [adjectives.get(f, f) for f in features]
        return f"Welcome to this exceptional {room_type}, where {', '.join(enhanced_features)} features create an unforgettable living space. This carefully designed area exemplifies luxury living at its finest."

    def __call__(self, room_type: str, features: list) -> str:
        """Convenience method to generate description"""
        return self.generate_description(room_type, features) 
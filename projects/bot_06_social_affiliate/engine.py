import os
import requests
import asyncio
import edge_tts
import uuid
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip

# Obter as chaves das Variáveis de Ambiente
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# Configurar Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

class VideoFactory:
    def __init__(self, output_dir="static/videos"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_script(self, niche):
        """Gera um guião viral de 15s-30s usando o Google Gemini"""
        if not gemini_model:
            return "Erro: Chave Gemini não configurada."
            
        prompt = f"""
        Escreve um guião para um vídeo curto (TikTok/Reels) de 20 segundos sobre o nicho/produto: '{niche}'.
        O idioma DEVE ser o Português (de Portugal ou Brasil, o mais natural e conversacional possível).
        O vídeo não vai ter pessoa a falar (é faceless), por isso o guião é apenas para a locução (Voiceover).
        
        Estrutura obrigatória:
        1. Gancho (Hook): Uma frase inicial chocante ou muito curiosa.
        2. Corpo: Explicação rápida de um problema e como o produto resolve.
        3. CTA (Call to Action): Mandar clicar no link da bio.
        
        NÃO incluas marcações de cena como [Música] ou [Cena muda]. Escreve APENAS o texto que vai ser lido em voz alta, de forma corrida e natural.
        """
        
        try:
            response = gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Erro no Gemini: {e}")
            return "Sabias que a maioria das pessoas perde grandes oportunidades todos os dias? Descobre como podes mudar isso agora. Clica no link da minha bio."

    async def generate_voiceover(self, script, filename):
        """Gera o ficheiro MP3 a partir do texto usando Microsoft Edge TTS"""
        voice = "pt-PT-DuarteNeural" # Voz masculina de Portugal (ou pt-BR-AntonioNeural)
        communicate = edge_tts.Communicate(script, voice)
        await communicate.save(filename)
        return filename

    def fetch_background_video(self, niche, filename):
        """Descarrega um vídeo vertical gratuito da API do Pexels"""
        if not PEXELS_API_KEY:
            print("Erro: Chave Pexels não configurada.")
            return None
            
        url = f"https://api.pexels.com/videos/search?query={niche}&orientation=portrait&size=medium&per_page=1"
        headers = {"Authorization": PEXELS_API_KEY}
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            if "videos" in data and len(data["videos"]) > 0:
                video_files = data["videos"][0]["video_files"]
                # Procurar o melhor link mp4
                video_url = None
                for vf in video_files:
                    if vf["file_type"] == "video/mp4":
                        video_url = vf["link"]
                        break
                
                if video_url:
                    r = requests.get(video_url, stream=True)
                    with open(filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                    return filename
        except Exception as e:
            print(f"Erro no Pexels: {e}")
        return None

    def assemble_video(self, video_path, audio_path, output_path):
        """Junta o vídeo e o áudio usando MoviePy"""
        try:
            video = VideoFileClip(video_path)
            audio = AudioFileClip(audio_path)
            
            # Se o áudio for mais comprido que o vídeo, cortamos o áudio (ou fazemos loop do vídeo)
            # Para a v1, vamos cortar o vídeo à medida do áudio se o vídeo for maior
            # Ou cortar o áudio se o vídeo for mais curto (para não ficar ecrã preto)
            
            final_duration = min(video.duration, audio.duration)
            
            video = video.subclip(0, final_duration)
            audio = audio.subclip(0, final_duration)
            
            final_video = video.set_audio(audio)
            
            # Escrever ficheiro final (fps baixo para renderizar rápido num servidor gratuito)
            final_video.write_videofile(
                output_path, 
                fps=24,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                logger=None
            )
            
            video.close()
            audio.close()
            final_video.close()
            return True
        except Exception as e:
            print(f"Erro na montagem do vídeo: {e}")
            return False

    def create_viral_video(self, niche):
        """Orquestrador principal que faz tudo"""
        job_id = str(uuid.uuid4())[:8]
        audio_path = os.path.join(self.output_dir, f"temp_{job_id}.mp3")
        bg_video_path = os.path.join(self.output_dir, f"temp_{job_id}.mp4")
        final_output_path = os.path.join(self.output_dir, f"viral_{job_id}.mp4")
        
        print(f"[{job_id}] 1. A gerar guião...")
        script = self.generate_script(niche)
        
        print(f"[{job_id}] 2. A gerar voz...")
        asyncio.run(self.generate_voiceover(script, audio_path))
        
        print(f"[{job_id}] 3. A descarregar vídeos de fundo...")
        # Simplificamos a pesquisa Pexels (usar a primeira palavra do nicho para ter mais resultados)
        search_query = niche.split()[0] if niche else "technology"
        bg_success = self.fetch_background_video(search_query, bg_video_path)
        
        if not bg_success:
            return {"status": "error", "message": "Não foi possível descarregar vídeo de fundo do Pexels."}
            
        print(f"[{job_id}] 4. A montar o MP4 final...")
        assemble_success = self.assemble_video(bg_video_path, audio_path, final_output_path)
        
        # Limpar temporários
        if os.path.exists(audio_path): os.remove(audio_path)
        if os.path.exists(bg_video_path): os.remove(bg_video_path)
        
        if assemble_success:
            return {
                "status": "success",
                "script": script,
                "video_url": f"/static/videos/viral_{job_id}.mp4"
            }
        else:
            return {"status": "error", "message": "Erro a renderizar o vídeo final."}

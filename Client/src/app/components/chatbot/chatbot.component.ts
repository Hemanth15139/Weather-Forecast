import { Component, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../services/chat.service';
import { WeatherService } from '../../services/weather.service';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="glass-panel rounded-3xl flex flex-col h-[750px] max-h-[85vh] relative overflow-hidden border border-white/10 shadow-2xl">
      
      <!-- Top Ambient AI Glow -->
      <div class="absolute -top-10 -left-10 w-48 h-48 bg-indigo-500/20 rounded-full blur-2xl pointer-events-none animate-pulse-glow"></div>

      <!-- Chatbot Header -->
      <div class="p-4 md:p-5 border-b border-white/10 flex items-center justify-between relative z-10 bg-slate-900/40">
        <div class="flex items-center gap-3">
          
          <!-- AI Avatar with Glowing Pulse -->
          <div class="relative">
            <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr from-sky-400 via-indigo-500 to-purple-500 p-0.5 shadow-lg">
              <div class="w-full h-full bg-slate-900 rounded-[14px] flex items-center justify-center text-sky-400 font-extrabold text-sm">
                AI
              </div>
            </div>
            <span class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 border-2 border-slate-900 rounded-full animate-ping"></span>
            <span class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 border-2 border-slate-900 rounded-full"></span>
          </div>

          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-white tracking-wide">Miracle AI Assistant</h2>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                LLM Ready
              </span>
            </div>
            <p class="text-[11px] text-slate-400 flex items-center gap-1.5">
              <span>Context:</span>
              <strong class="text-sky-300 font-medium">{{ weatherService.selectedLocation().name }}</strong>
            </p>
          </div>

        </div>

        <!-- Header Actions: Voice & Clear -->
        <div class="flex items-center gap-2">
          <button
            (click)="chatService.toggleVoice()"
            [class.bg-rose-500/20]="chatService.isVoiceActive()"
            [class.text-rose-300]="chatService.isVoiceActive()"
            [class.border-rose-500/40]="chatService.isVoiceActive()"
            title="Toggle Voice Input Mode"
            class="p-2 rounded-xl glass-card text-slate-400 hover:text-white transition-all text-xs flex items-center gap-1.5"
          >
            <svg class="w-4 h-4" [class.animate-pulse]="chatService.isVoiceActive()" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            <span class="hidden sm:inline text-[11px]">{{ chatService.isVoiceActive() ? 'Mic On' : 'Voice' }}</span>
          </button>

          <button
            (click)="chatService.clearChat()"
            title="Clear Chat History"
            class="p-2 rounded-xl glass-card text-slate-400 hover:text-rose-400 transition-all"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Quick Prompt Suggestion Chips -->
      <div class="px-4 py-2.5 border-b border-white/5 bg-slate-900/20 flex items-center gap-2 overflow-x-auto scrollbar-none">
        <span class="text-[10px] text-slate-400 font-bold uppercase shrink-0">Prompts:</span>
        @for (prompt of samplePrompts; track prompt) {
          <button
            (click)="sendQuickPrompt(prompt)"
            class="px-3 py-1 rounded-full glass-card text-[11px] text-slate-300 hover:text-white hover:border-sky-400/50 whitespace-nowrap transition-all shrink-0 active:scale-95"
          >
            {{ prompt }}
          </button>
        }
      </div>

      <!-- Chat Feed Container -->
      <div #chatContainer class="flex-1 p-4 overflow-y-auto space-y-4 relative scrollbar-thin">
        @for (msg of chatService.messages(); track msg.id) {
          
          <!-- User Message -->
          @if (msg.sender === 'user') {
            <div class="flex justify-end items-end gap-2">
              <div class="max-w-[82%] bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-2xl rounded-br-sm p-3.5 shadow-lg text-xs md:text-sm font-normal leading-relaxed">
                <p class="whitespace-pre-wrap">{{ msg.text }}</p>
                <div class="text-[10px] text-sky-100/70 text-right mt-1 font-mono">
                  {{ msg.timestamp | date:'shortTime' }}
                </div>
              </div>
            </div>
          }

          <!-- AI Assistant Message -->
          @if (msg.sender === 'assistant') {
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center text-sky-400 text-xs font-bold shrink-0 mt-0.5">
                🤖
              </div>

              <div class="max-w-[86%] space-y-2">
                <div class="glass-card rounded-2xl rounded-tl-sm p-4 text-xs md:text-sm text-slate-200 leading-relaxed border-white/10 shadow-md">
                  
                  <!-- Formatted Text (Supports bolding & linebreaks) -->
                  <div class="whitespace-pre-line" [innerHTML]="formatMarkdown(msg.text)"></div>

                  <!-- Embedded Weather Snapshot Card (if available) -->
                  @if (msg.weatherSnapshot; as snap) {
                    <div class="mt-3 p-3 rounded-xl bg-slate-900/60 border border-sky-500/20 text-xs space-y-1">
                      <div class="flex items-center justify-between font-bold text-sky-300">
                        <span>📍 {{ snap.location }} Weather Brief</span>
                        <span class="text-white font-extrabold">{{ snap.temp }}</span>
                      </div>
                      <div class="text-slate-400 text-[11px]">
                        Condition: <strong class="text-slate-200">{{ snap.condition }}</strong> • Humidity: {{ snap.humidity }}
                      </div>
                      @if (snap.recommendation) {
                        <div class="pt-1 text-[11px] text-amber-300 font-medium">
                          💡 Advice: {{ snap.recommendation }}
                        </div>
                      }
                    </div>
                  }

                </div>

                <div class="flex items-center gap-3 text-[10px] text-slate-400 px-1">
                  <span>{{ msg.timestamp | date:'shortTime' }}</span>
                  <button (click)="copyToClipboard(msg.text)" class="hover:text-white transition-colors">
                    Copy
                  </button>
                </div>
              </div>
            </div>
          }

        }

        <!-- AI Typing Indicator -->
        @if (chatService.isTyping()) {
          <div class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center text-sky-400 text-xs font-bold shrink-0">
              🤖
            </div>
            <div class="glass-card rounded-2xl p-3.5 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-sky-400 animate-bounce"></span>
              <span class="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.2s]"></span>
              <span class="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.4s]"></span>
              <span class="text-xs text-slate-400 font-medium ml-1">Analyzing weather metrics & LLM context...</span>
            </div>
          </div>
        }
      </div>

      <!-- Voice Listening Active Indicator Banner -->
      @if (chatService.isVoiceActive()) {
        <div class="px-4 py-2 bg-rose-500/10 border-t border-rose-500/20 text-rose-300 text-xs flex items-center justify-between animate-pulse">
          <span class="flex items-center gap-2 font-medium">
            <span class="w-2 h-2 rounded-full bg-rose-400"></span>
            Listening... Speak now (Mock Audio Capture Active)
          </span>
          <button (click)="chatService.toggleVoice()" class="text-xs font-bold underline hover:text-white">
            Stop
          </button>
        </div>
      }

      <!-- Bottom Chat Input Bar -->
      <div class="p-3 md:p-4 border-t border-white/10 bg-slate-900/60 relative z-10">
        <form (ngSubmit)="sendUserMessage()" class="flex items-center gap-2">
          
          <input
            type="text"
            [(ngModel)]="userPrompt"
            name="userPrompt"
            [disabled]="chatService.isTyping()"
            placeholder="Ask AI Weather Assistant (e.g. Should I pack an umbrella?)..."
            class="flex-1 glass-input rounded-2xl px-4 py-3 text-xs md:text-sm focus:outline-none transition-all"
          />

          <!-- Send Button -->
          <button
            type="submit"
            [disabled]="!userPrompt.trim() || chatService.isTyping()"
            class="px-4 py-3 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold text-xs flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md active:scale-95 shrink-0"
          >
            <span>Send</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>

        </form>

        <div class="mt-2 text-[10px] text-slate-400 text-center flex items-center justify-center gap-1.5">
          <span>Connected to backend: <code class="text-sky-300 font-mono">http://localhost:8000/api/chat</code></span>
        </div>
      </div>

    </div>
  `
})
export class ChatbotComponent implements AfterViewChecked {
  @ViewChild('chatContainer') private chatContainer!: ElementRef;
  userPrompt = '';

  samplePrompts = [
    'What should I wear today?',
    'Will it rain in my city?',
    'Give me travel & packing tips',
    'Is AQI safe for outdoor run?'
  ];

  constructor(
    public chatService: ChatService,
    public weatherService: WeatherService
  ) { }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  sendUserMessage(): void {
    if (!this.userPrompt.trim()) return;
    const text = this.userPrompt;
    this.userPrompt = '';
    this.chatService.sendMessage(text);
  }

  sendQuickPrompt(prompt: string): void {
    this.chatService.sendMessage(prompt);
  }

  formatMarkdown(text: string): string {
    if (!text) return '';
    // Simple markdown formatter for bolding **text** and linebreaks
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-bold">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="text-sky-200">$1</em>');
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text);
  }

  private scrollToBottom(): void {
    try {
      this.chatContainer.nativeElement.scrollTop =
        this.chatContainer.nativeElement.scrollHeight;
    } catch (err) { }
  }
}

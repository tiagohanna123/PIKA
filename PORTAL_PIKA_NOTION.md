# Portal PIKA

## Visão Geral

O **Portal PIKA** é uma interface web interativa para executar e visualizar simulações do Framework PIKA em tempo real. Construído em Dash/Plotly, permite experimentação imediata de diferentes cenários e configurações sem necessidade de programação.

**Status**: Branch `feature/portal-ux-improvements` — Atualizações de UX e usabilidade implementadas.

---

## Melhorias Recentes de UX

### 1. **Limpeza Visual dos Sliders**

- ✅ Remoção de labels sobrepostos nos eixos dos sliders
- ✅ Tooltips na base do slider mostrando valor ao arrastar
- ✅ Interface limpa e legível sem visual clutter

### 2. **5 Presets de Controle Pré-ajustados**

Carregue configurações completas com um clique:

| Preset | Descrição | Ideal Para |
|--------|-----------|-----------|
| **Fechado (X → 0)** | Sistema sem ruído e sem bomba; ondas sintropicas ajustam para X tender a 0 frente à força entrópica | Estudar equilíbrio dinâmico |
| **Equilíbrio ao vivo** | Dinâmica fluida com dt menor, ondas moderadas e pouco ruído | Modo ao vivo (live mode) |
| **Entropia domina** | Força entrópica alta e sintropia baixa; X tende a ficar negativo | Visualizar dissipação |
| **Sintropia domina** | Ondas organizadoras fortes; padrões e estruturas emergem | Ver formação de padrões |
| **Exploração (η)** | Mais ruído estocástico; útil para ver transições e instabilidades | Análise de bifurcações |

### 3. **Tooltips Explicativos Inteligentes**

Todos os ~25 controles possuem um ícone **(i)** que explica:

- **O que** cada parâmetro faz no sistema
- **Como** impacta X, Φs, Φσ e energia
- **Dicas práticas** de uso

**Exemplos:**

- **dt**: "Controla a resolução temporal. dt menor = dinâmica mais suave/estável, porém mais lenta"
- **wave_gain**: "Aumentar acelera correção para X→0, mas pode gerar oscilação se muito alto"
- **noise_sigma**: "Intensidade do ruído estocástico η. Aumenta exploração e variabilidade"
- **coupling_alpha**: "Força de acoplamento entre pontos. Faz o sistema agir de forma mais coletiva"

---

## Como Usar

### Fluxo Rápido

1. **Escolha um preset** no dropdown "Preset de controle" para carregar configuração padrão
2. **Ajuste finamente** os parâmetros que quiser
3. **Passe o mouse** sobre o **(i)** ao lado de qualquer label para entender o impacto
4. **Execute**: Clique "Rodar simulação" para execução completa ou ative "Modo ao vivo" para visualizar em tempo real

### Seções da Interface

#### **Guia Rápido** (expandível)

- Instruções essenciais
- Definição de termos (Entropia, Sintropia, X)

#### **Presets**

- Dropdown com 5 configurações pré-ajustadas
- Descrição automática da configuração selecionada

#### **Cenário**

- **Core**: Núcleo PIKA (Sintropia ↔ Entropia)
- **Finance**: Mercados com ciclos e choques
- **Biology**: Dinâmica homeostática
- **Fluids**: Fluxo coletivo com acoplamento

#### **Tempo**

- **dt**: Passo de integração (menor = mais suave, mais lento)
- **steps**: Número de iterações (horizonte temporal)
- **points**: Número de partículas (mais = campo mais rico, mais pesado)
- **seed**: Controla reprodutibilidade (opcional)

#### **Processos**

- **Bomba interna** (pump_power): Fonte de energia interna
- **Atração ao objetivo** (goal_k): Força organizadora
- **Viscosidade** (viscosity_mu): Amortecimento/dissipação
- **Barreira** (barrier_k, barrier_radius): Organização espacial
- **Ruído** (noise_sigma): Exploração estocástica
- **Acoplamento** (coupling_alpha, coupling_length): Coletividade
- **Regulador** (regulator_gain): Feedback para X→0

#### **Entropia e Sintropia**

- **Entropia**: Força constante com magnitude e ângulo ajustáveis
- **Sintropia**: Ondas organizadoras com ganho, frequência espacial (k) e temporal (omega)

#### **Opções**

- Toggles para incluir/excluir componentes (ruído, acoplamento, regulador)
- Integração cinemática (posição = posição + dt × velocidade)

---

## Visualizações

### Timeseries

Gráfico temporal mostrando:

- **X = Φs − Φσ**: Estado resultante do sistema
- **Φs**: Taxa sintrópica (organização)
- **Φσ**: Taxa entrópica (dissipação)
- **E_total**: Energia total do sistema

### Campo 2D

Vista de cima mostrando:

- **Pontos**: Posições das partículas (coloridas por energia interna)
- **Vetores de velocidade**: Setas indicando direção e magnitude
- **Escala**: Ajustável via slider "Escala do vetor"

### Campo 3D

Perspectiva 3D com:

- **Eixo Z**: Energia interna das partículas
- **Vetores 3D**: Componentes XY (velocidade) + Z (magnitude da velocidade)
- **Escala Z**: Ajustável via slider "Escala vertical"

### Passo de Visualização

- Slider "Passo de visualização": Escolhe qual frame dos históricos será mostrado nos gráficos 2D/3D
- Não re-simula; apenas troca o frame exibido

---

## Modo Ao Vivo (Live Mode)

### Funcionalidade

- Executa **um passo por tick** do dcc.Interval
- Mantém estado contínuo do RNG (randomness) entre ticks
- Útil para ver dinâmica em tempo real

### Controles

- **Botão "Modo ao vivo"**: Inicia/para execução
- **Intervalo**: Define ms entre ticks (50 ms a 2000 ms)
- **Status**: Exibe estado atual e intervalo ativo

### Dicas

- Use preset "Equilíbrio ao vivo" para melhor experiência
- Diminua intervalo para dinâmica mais fluida (cuidado com CPU/navegador)
- Observe Φs e Φσ convergirem em padrões oscilatórios

---

## Matemática Implementada

### Equação Fundamental

$$\frac{dX}{dt} = S(t) - H(t) + \eta(t)$$

Onde:
- **X(t)**: Estado resultante do sistema
- **S(t)** (Φs): Taxa sintrópica (organização)
- **H(t)** (Φσ): Taxa entrópica (dissipação)
- **η(t)**: Termo estocástico (ruído)

### Energia do Sistema

$$E_{total} = E_{kinetic} + E_{internal}$$

$$E_{kinetic} = \frac{1}{2}m v^2$$

### Processos e Contribuições

Cada processo retorna uma contribuição com:
- `energy_rate`: Taxa de energia (positivo = sintrópico, negativo = entrópico)
- `velocity_delta`: Aceleração a aplicar (Δv)

### Fluxo como Supraprocesso

$$\Phi(t) = \sum_{i=1}^{n} \phi_i(t) = S_{total}(t) - H_{total}(t)$$

Cada processo contribui para o fluxo total através da superposição de energia e momento.

### Integração Temporal

Semi-implícita (Forward Euler):

1. Calcular todas as contribuições dos processos
2. Agregar em Φs e Φσ
3. Atualizar velocidade e energia: `v' = v + dt × Δv`; `E' = E + dt × energy_rate`
4. Opcional: integrar posição: `r' = r + dt × v'`

---

## Arquitetura Técnica

### Stack

- **Backend**: Python 3.13.1, Dash 3.3.0, Plotly
- **Simulator**: Framework PIKA legacy (core, process, flow)
- **Estado**: dcc.Store para dados de simulação e live mode
- **Persistência**: localStorage (opcional, atualmente desativada)

### Componentes Principais

| Arquivo | Função |
|---------|--------|
| `app.py` | Aplicação Dash, callbacks, layout, presets |
| `scenarios.py` | Definição de 4 cenários, build_flow |
| `simulation.py` | run_simulation, live mode stepping |

### 7 Processos Implementados

1. **InternalPump**: Fonte de energia (pump_power)
2. **GoalAttraction**: Atração ao objetivo (goal_k)
3. **Viscosity**: Amortecimento/dissipação (viscosity_mu)
4. **OrganizationBarrier**: Barreira repulsiva (barrier_k, barrier_radius)
5. **NoiseExploration**: Ruído estocástico (noise_sigma)
6. **CouplingKernel**: Acoplamento entre vizinhos (coupling_alpha, coupling_length)
7. **SyntropyWaveRegulator**: Ondas organizadoras adaptivas (wave_gain, k, omega)

### EntropyForce

- Vetor constante de força entrópica
- Magnitude e ângulo ajustáveis
- Implementado como processo adicional quando não selecionado o regulador

---

## Benefícios

| Benefício | Impacto |
|-----------|--------|
| **Menor curva de aprendizado** | Presets permitem começar imediatamente |
| **Auto-descoberta** | Tooltips explicam cada parâmetro sem sair |
| **Interface limpa** | Sem visual clutter; foco no comportamento |
| **Experimentos rápidos** | 5 configurações prontas para diferentes dinâmicas |
| **Visualização 3D** | Compreensão intuitiva de campo + energia |
| **Live mode** | Observar evolução em tempo real |
| **Reprodutibilidade** | Seed permite experimentos determinísticos |
| **Validação matemática** | Código alinhado 100% com teoria |

---

## Status Técnico

- ✅ Todos os testes de regressão passando (4/4)
- ✅ Portal executando em http://127.0.0.1:8050
- ✅ Branch: `feature/portal-ux-improvements`
- ✅ Sem novas dependências adicionadas
- ✅ Código alinhado com formulação matemática
- ✅ Ready for PR ao `main`

---

## Próximos Passos

1. **Merge** da branch `feature/portal-ux-improvements` para `main`
2. **Documentação** de casos de uso típicos
3. **Validação empírica** com dados reais (finanças, biologia)
4. **Otimização** de performance para +100 pontos

---

*Última atualização: 23 de dezembro de 2025*

import os
import pickle
import datetime
from typing import List, Dict, Optional

class Pedido:
    def __init__(self, numero: int, cliente: str, sabor: str, tamanho: str = "Média",
                 adicional: List[str] = None, observacoes: str = "",
                 data_hora: datetime.datetime = None):
        self.numero = numero
        self.cliente = cliente
        self.sabor = sabor
        self.tamanho = tamanho
        self.adicional = adicional or []
        self.observacoes = observacoes
        self.data_hora = data_hora or datetime.datetime.now()
        self.status = "Pendente"
        self.tempo_preparo = self._calcular_tempo_preparo()

    def _calcular_tempo_preparo(self) -> int:
        """Calcula o tempo estimado de preparo em minutos"""
        tempo_base = {
            "Pequena": 15,
            "Média": 20,
            "Grande": 25,
            "Família": 30
        }
        tempo = tempo_base.get(self.tamanho, 20)
        # Adiciona 2 minutos para cada adicional
        tempo += len(self.adicional) * 2
        return tempo

    def __str__(self) -> str:
        adicionais = ", ".join(self.adicional) if self.adicional else "Nenhum"
        return (f"Pedido #{self.numero} | Cliente: {self.cliente} | "
                f"Pizza: {self.sabor} ({self.tamanho}) | "
                f"Adicionais: {adicionais} | Status: {self.status}")


class SistemaPizzaria:
    def __init__(self, arquivo_pedidos: str = "pedidos.pickle",
                 arquivo_cardapio: str = "cardapio.pickle"):
        self.arquivo_pedidos = arquivo_pedidos
        self.arquivo_cardapio = arquivo_cardapio
        self.fila_pedidos: List[Pedido] = []
        self.contador_pedidos: int = 1
        self.cardapio: Dict[str, Dict] = self._inicializar_cardapio()
        self.historico_pedidos: List[Pedido] = []
        self.carregar_dados()

    def _inicializar_cardapio(self) -> Dict:
        """Inicializa o cardápio base se não existir"""
        cardapio_padrao = {
            "sabores": {
                "Marguerita": {"ingredientes": ["Molho de tomate", "Muçarela", "Manjericão"], "preco": {"Pequena": 30, "Média": 40, "Grande": 52, "Família": 60}},
                "Calabresa": {"ingredientes": ["Molho de tomate", "Muçarela", "Calabresa", "Cebola"], "preco": {"Pequena": 32, "Média": 42, "Grande": 50, "Família": 62}},
                "Frango c/ Catupiry": {"ingredientes": ["Molho de tomate", "Muçarela", "Frango", "Catupiry"], "preco": {"Pequena": 35, "Média": 45, "Grande": 58, "Família": 65}},
                "Portuguesa": {"ingredientes": ["Molho de tomate", "Muçarela", "Presunto", "Ovos", "Cebola", "Ervilha"], "preco": {"Pequena": 38, "Média": 48, "Grande": 55, "Família": 68}},
                "Quatro Queijos": {"ingredientes": ["Molho de tomate", "Muçarela", "Parmesão", "Provolone", "Gorgonzola"], "preco": {"Pequena": 40, "Média": 50, "Grande": 60, "Família": 70}},
                "Presunto": {"ingredientes": ["Molho de tomate", "Presunto", "Muçarela", "Rodelas de tomate"], "preco": {"Pequena": 30, "Média": 35, "Grande": 45, "Família":50}},
                "Bacon": {"ingredientes": ["Molho de tomate", "Muçarela", "Bacon", "Rodelas de tomate"], "preco": {"Pequena": 35, "Média": 45, "Grande": 55, "Família": 65}},
                "Napolitana": {"ingredientes": ["Molho de tomate", "Muçarela", "Rodelas  de tomate", "Parmesão ralado"], "preco": {"Pequena": 40, "Média": 50, "Grande": 60, "Família": 70}}

            },
            "adicionais": {
                "Borda recheada": 8,
                "Catupiry extra": 5,
                "Cheddar extra": 5,
                "Bacon": 6,
                "Azeitona": 3,
                "Palmito": 7
            },
            "tamanhos": ["Pequena", "Média", "Grande", "Família"]
        }
        return cardapio_padrao

    def salvar_dados(self) -> None:
        """Salva pedidos e cardápio em arquivos"""
        with open(self.arquivo_pedidos, "wb") as f:
            dados = {
                "fila_pedidos": self.fila_pedidos,
                "contador_pedidos": self.contador_pedidos,
                "historico_pedidos": self.historico_pedidos
            }
            pickle.dump(dados, f)

        with open(self.arquivo_cardapio, "wb") as f:
            pickle.dump(self.cardapio, f)

    def carregar_dados(self) -> None:
        """Carrega pedidos e cardápio de arquivos"""
        # Carrega pedidos
        if os.path.exists(self.arquivo_pedidos):
            try:
                with open(self.arquivo_pedidos, "rb") as f:
                    dados = pickle.load(f)
                    self.fila_pedidos = dados.get("fila_pedidos", [])
                    self.contador_pedidos = dados.get("contador_pedidos", 1)
                    self.historico_pedidos = dados.get("historico_pedidos", [])
            except (pickle.PickleError, EOFError):
                print("⚠️ Erro ao carregar pedidos. Iniciando sistema com dados vazios.")

        # Carrega cardápio
        if os.path.exists(self.arquivo_cardapio):
            try:
                with open(self.arquivo_cardapio, "rb") as f:
                    self.cardapio = pickle.load(f)
            except (pickle.PickleError, EOFError):
                print("⚠️ Erro ao carregar cardápio. Usando cardápio padrão.")

    def adicionar_pedido(self) -> None:
        """Adiciona um novo pedido à fila"""
        print("\n=== Novo Pedido ===")

        # Informações do cliente
        nome_cliente = input("Nome do cliente: ")
        telefone = input("Telefone para contato: ")

        # Mostra opções de sabores
        print("\n--- Sabores disponíveis ---")
        for i, sabor in enumerate(self.cardapio["sabores"].keys(), 1):
            print(f"{i}. {sabor}")

        opcao = int(input("\nEscolha o número do sabor: ")) - 1
        sabores = list(self.cardapio["sabores"].keys())
        if opcao < 0 or opcao >= len(sabores):
            print("⚠️ Opção inválida! Usando primeiro sabor disponível.")
            opcao = 0
        sabor_pizza = sabores[opcao]

        # Mostra ingredientes
        print(f"\nIngredientes: {', '.join(self.cardapio['sabores'][sabor_pizza]['ingredientes'])}")

        # Escolha do tamanho
        print("\n--- Tamanhos disponíveis ---")
        for i, tamanho in enumerate(self.cardapio["tamanhos"], 1):
            preco = self.cardapio["sabores"][sabor_pizza]["preco"][tamanho]
            print(f"{i}. {tamanho} - R$ {preco:.2f}")

        opcao = int(input("\nEscolha o número do tamanho: ")) - 1
        if opcao < 0 or opcao >= len(self.cardapio["tamanhos"]):
            print("⚠️ Opção inválida! Usando tamanho médio.")
            opcao = 1
        tamanho = self.cardapio["tamanhos"][opcao]

        # Adicionais
        adicionais = []
        print("\n--- Adicionais disponíveis ---")
        for i, (adicional, preco) in enumerate(self.cardapio["adicionais"].items(), 1):
            print(f"{i}. {adicional} - R$ {preco:.2f}")

        escolha = input("\nDeseja adicionar algum adicional? (S/N): ").strip().upper()
        if escolha == "S":
            while True:
                opcao = int(input("Digite o número do adicional (0 para finalizar): "))
                if opcao == 0:
                    break

                if opcao < 1 or opcao > len(self.cardapio["adicionais"]):
                    print("⚠️ Opção inválida!")
                    continue

                adicional = list(self.cardapio["adicionais"].keys())[opcao-1]
                adicionais.append(adicional)
                print(f"✅ {adicional} adicionado!")

        # Observações
        observacoes = input("\nObservações adicionais: ")

        # Calcula valor total
        valor_base = self.cardapio["sabores"][sabor_pizza]["preco"][tamanho]
        valor_adicionais = sum(self.cardapio["adicionais"][a] for a in adicionais)
        valor_total = valor_base + valor_adicionais

        # Confirmação do pedido
        print("\n=== Resumo do Pedido ===")
        print(f"Cliente: {nome_cliente}")
        print(f"Telefone: {telefone}")
        print(f"Pizza: {sabor_pizza} ({tamanho})")
        print(f"Adicionais: {', '.join(adicionais) if adicionais else 'Nenhum'}")
        if observacoes:
            print(f"Observações: {observacoes}")
        print(f"Valor total: R$ {valor_total:.2f}")

        confirma = input("\nConfirmar pedido? (S/N): ").strip().upper()
        if confirma != "S":
            print("❌ Pedido cancelado!")
            return

        # Cria o novo pedido
        novo_pedido = Pedido(
            numero=self.contador_pedidos,
            cliente=f"{nome_cliente} ({telefone})",
            sabor=sabor_pizza,
            tamanho=tamanho,
            adicional=adicionais,
            observacoes=observacoes
        )

        # Incrementa o contador e adiciona à fila
        self.contador_pedidos += 1
        self.fila_pedidos.append(novo_pedido)
        self.salvar_dados()

        print(f"\n✅ Pedido #{novo_pedido.numero} registrado com sucesso!")
        print(f"⏱️ Tempo estimado de preparo: {novo_pedido.tempo_preparo} minutos")

    def visualizar_fila(self) -> None:
        """Exibe a fila de pedidos atual"""
        if not self.fila_pedidos:
            print("📭 Nenhum pedido na fila!")
            return

        print("\n📋 == FILA DE PEDIDOS ==")
        for i, pedido in enumerate(self.fila_pedidos, 1):
            tempo_espera = (datetime.datetime.now() - pedido.data_hora).total_seconds() // 60
            print(f"{i}. {pedido}")
            print(f"   ⏱️ Aguardando há {int(tempo_espera)} minutos | Preparo: {pedido.tempo_preparo} min")
            if pedido.observacoes:
                print(f"   📝 Obs: {pedido.observacoes}")
            print()

    def entregar_pedido(self) -> None:
        """Remove o primeiro pedido da fila (FIFO)"""
        if not self.fila_pedidos:
            print("🚫 Nenhum pedido na fila!")
            return

        # Mostra os pedidos pendentes
        self.visualizar_fila()

        # Pergunta qual pedido entregar (por padrão, o primeiro)
        escolha = input("Digite o número da posição do pedido a entregar (1 para o primeiro): ")

        # Se não informar, entrega o primeiro
        if not escolha:
            posicao = 0
        else:
            posicao = int(escolha) - 1

        if posicao < 0 or posicao >= len(self.fila_pedidos):
            print("⚠️ Posição inválida!")
            return

        # Remove o pedido da fila
        pedido_entregue = self.fila_pedidos.pop(posicao)
        pedido_entregue.status = "Entregue"

        # Adiciona ao histórico
        self.historico_pedidos.append(pedido_entregue)

        # Salva os dados
        self.salvar_dados()

        print(f"🍕 Pedido #{pedido_entregue.numero} de {pedido_entregue.cliente} foi entregue!")

    def alterar_pedido(self) -> None:
        """Altera informações de um pedido"""
        if not self.fila_pedidos:
            print("🚫 Nenhum pedido na fila!")
            return

        numero_pedido = int(input("Digite o número do pedido que deseja alterar: "))

        pedido = None
        for p in self.fila_pedidos:
            if p.numero == numero_pedido:
                pedido = p
                break

        if not pedido:
            print("⚠️ Pedido não encontrado!")
            return

        print(f"\nEditando pedido #{pedido.numero}")
        print("O que deseja alterar?")
        print("1. Sabor da pizza")
        print("2. Tamanho da pizza")
        print("3. Adicionais")
        print("4. Observações")
        print("5. Status")

        opcao = input("Escolha uma opção (ou ENTER para cancelar): ")
        if not opcao:
            return

        if opcao == "1":  # Alterar sabor
            print("\n--- Sabores disponíveis ---")
            for i, sabor in enumerate(self.cardapio["sabores"].keys(), 1):
                print(f"{i}. {sabor}")

            escolha = int(input(f"\nEscolha o novo sabor (atual: {pedido.sabor}): ")) - 1
            sabores = list(self.cardapio["sabores"].keys())
            if escolha < 0 or escolha >= len(sabores):
                print("⚠️ Opção inválida!")
                return

            pedido.sabor = sabores[escolha]
            print(f"✅ Sabor alterado para {pedido.sabor}")

        elif opcao == "2":  # Alterar tamanho
            print("\n--- Tamanhos disponíveis ---")
            for i, tamanho in enumerate(self.cardapio["tamanhos"], 1):
                preco = self.cardapio["sabores"][pedido.sabor]["preco"][tamanho]
                print(f"{i}. {tamanho} - R$ {preco:.2f}")

            escolha = int(input(f"\nEscolha o novo tamanho (atual: {pedido.tamanho}): ")) - 1
            if escolha < 0 or escolha >= len(self.cardapio["tamanhos"]):
                print("⚠️ Opção inválida!")
                return

            pedido.tamanho = self.cardapio["tamanhos"][escolha]
            pedido.tempo_preparo = pedido._calcular_tempo_preparo()
            print(f"✅ Tamanho alterado para {pedido.tamanho}")

        elif opcao == "3":  # Alterar adicionais
            print("\nAdicionais atuais:", ", ".join(pedido.adicional) if pedido.adicional else "Nenhum")
            print("\n--- Adicionais disponíveis ---")
            for i, (adicional, preco) in enumerate(self.cardapio["adicionais"].items(), 1):
                print(f"{i}. {adicional} - R$ {preco:.2f}")

            print("\n1. Adicionar mais itens")
            print("2. Remover itens")
            print("3. Substituir todos")

            escolha = input("Escolha uma opção: ")

            if escolha == "1":  # Adicionar mais
                while True:
                    opcao_add = int(input("Digite o número do adicional (0 para finalizar): "))
                    if opcao_add == 0:
                        break

                    if opcao_add < 1 or opcao_add > len(self.cardapio["adicionais"]):
                        print("⚠️ Opção inválida!")
                        continue

                    adicional = list(self.cardapio["adicionais"].keys())[opcao_add-1]
                    if adicional not in pedido.adicional:
                        pedido.adicional.append(adicional)
                        print(f"✅ {adicional} adicionado!")
                    else:
                        print(f"⚠️ {adicional} já estava na lista!")

            elif escolha == "2":  # Remover itens
                if not pedido.adicional:
                    print("⚠️ Não há adicionais para remover!")
                    return

                for i, adicional in enumerate(pedido.adicional, 1):
                    print(f"{i}. {adicional}")

                opcao_rem = int(input("Digite o número do adicional a remover: "))
                if opcao_rem < 1 or opcao_rem > len(pedido.adicional):
                    print("⚠️ Opção inválida!")
                    return

                removido = pedido.adicional.pop(opcao_rem-1)
                print(f"✅ {removido} removido!")

            elif escolha == "3":  # Substituir todos
                novos_adicionais = []
                while True:
                    opcao_add = int(input("Digite o número do adicional (0 para finalizar): "))
                    if opcao_add == 0:
                        break

                    if opcao_add < 1 or opcao_add > len(self.cardapio["adicionais"]):
                        print("⚠️ Opção inválida!")
                        continue

                    adicional = list(self.cardapio["adicionais"].keys())[opcao_add-1]
                    if adicional not in novos_adicionais:
                        novos_adicionais.append(adicional)
                        print(f"✅ {adicional} adicionado!")

                pedido.adicional = novos_adicionais
                print("✅ Adicionais substituídos!")

            pedido.tempo_preparo = pedido._calcular_tempo_preparo()

        elif opcao == "4":  # Alterar observações
            print(f"Observações atuais: {pedido.observacoes}")
            novas_obs = input("Digite as novas observações: ")
            pedido.observacoes = novas_obs
            print("✅ Observações atualizadas!")

        elif opcao == "5":  # Alterar status
            print("\n--- Status disponíveis ---")
            status_disponiveis = ["Pendente", "Em preparo", "Saiu para entrega"]
            for i, status in enumerate(status_disponiveis, 1):
                print(f"{i}. {status}")

            escolha = int(input(f"\nEscolha o novo status (atual: {pedido.status}): ")) - 1
            if escolha < 0 or escolha >= len(status_disponiveis):
                print("⚠️ Opção inválida!")
                return

            pedido.status = status_disponiveis[escolha]
            print(f"✅ Status alterado para {pedido.status}")

        else:
            print("⚠️ Opção inválida!")
            return

        # Salva as alterações
        self.salvar_dados()
        print("✅ Pedido atualizado com sucesso!")

    def consultar_pedido(self) -> None:
        """Consulta detalhes de um pedido específico"""
        numero_pedido = int(input("Informe o número do pedido que deseja consultar: "))

        # Procura na fila atual
        for pedido in self.fila_pedidos:
            if pedido.numero == numero_pedido:
                self._exibir_detalhes_pedido(pedido)
                return

        # Procura no histórico
        for pedido in self.historico_pedidos:
            if pedido.numero == numero_pedido:
                self._exibir_detalhes_pedido(pedido)
                print("📝 Nota: Este pedido já foi entregue e está no histórico.")
                return

        print("⚠️ Pedido não encontrado.")

    def _exibir_detalhes_pedido(self, pedido: Pedido) -> None:
        """Exibe detalhes formatados de um pedido"""
        print("\n=== DETALHES DO PEDIDO ===")
        print(f"Número: #{pedido.numero}")
        print(f"Cliente: {pedido.cliente}")
        print(f"Data/Hora: {pedido.data_hora.strftime('%d/%m/%Y %H:%M')}")
        print(f"Status: {pedido.status}")
        print(f"Pizza: {pedido.sabor} ({pedido.tamanho})")

        # Mostra ingredientes
        if pedido.sabor in self.cardapio["sabores"]:
            ingredientes = self.cardapio["sabores"][pedido.sabor]["ingredientes"]
            print(f"Ingredientes: {', '.join(ingredientes)}")

        # Adicionais
        if pedido.adicional:
            print(f"Adicionais: {', '.join(pedido.adicional)}")

        # Observações
        if pedido.observacoes:
            print(f"Observações: {pedido.observacoes}")

        # Informações de tempo
        tempo_espera = (datetime.datetime.now() - pedido.data_hora).total_seconds() // 60
        print(f"Tempo de espera: {int(tempo_espera)} minutos")
        print(f"Tempo estimado de preparo: {pedido.tempo_preparo} minutos")

        # Valor (se disponível)
        if pedido.sabor in self.cardapio["sabores"] and pedido.tamanho in self.cardapio["sabores"][pedido.sabor]["preco"]:
            valor_base = self.cardapio["sabores"][pedido.sabor]["preco"][pedido.tamanho]
            valor_adicionais = sum(self.cardapio["adicionais"].get(a, 0) for a in pedido.adicional)
            valor_total = valor_base + valor_adicionais
            print(f"Valor total: R$ {valor_total:.2f}")

    def gerenciar_cardapio(self) -> None:
        """Permite gerenciar o cardápio"""
        print("\n=== GERENCIAMENTO DO CARDÁPIO ===")
        print("1. Ver cardápio completo")
        print("2. Adicionar novo sabor")
        print("3. Adicionar novo adicional")
        print("4. Modificar preços")
        print("5. Remover item")
        print("6. Voltar")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":  # Ver cardápio
            self._mostrar_cardapio()

        elif opcao == "2":  # Adicionar sabor
            nome_sabor = input("Nome do novo sabor: ")
            if nome_sabor in self.cardapio["sabores"]:
                print("⚠️ Este sabor já existe!")
                return

            ingredientes = input("Ingredientes (separados por vírgula): ").split(",")
            ingredientes = [i.strip() for i in ingredientes]

            precos = {}
            for tamanho in self.cardapio["tamanhos"]:
                try:
                    preco = float(input(f"Preço para tamanho {tamanho}: R$ "))
                    precos[tamanho] = preco
                except ValueError:
                    print("⚠️ Preço inválido! Use apenas números.")
                    return

            self.cardapio["sabores"][nome_sabor] = {
                "ingredientes": ingredientes,
                "preco": precos
            }

            self.salvar_dados()
            print(f"✅ Sabor {nome_sabor} adicionado ao cardápio!")

        elif opcao == "3":  # Adicionar adicional
            nome_adicional = input("Nome do novo adicional: ")
            if nome_adicional in self.cardapio["adicionais"]:
                print("⚠️ Este adicional já existe!")
                return

            try:
                preco = float(input(f"Preço do adicional: R$ "))
                self.cardapio["adicionais"][nome_adicional] = preco
                self.salvar_dados()
                print(f"✅ Adicional {nome_adicional} adicionado ao cardápio!")
            except ValueError:
                print("⚠️ Preço inválido! Use apenas números.")

        elif opcao == "4":  # Modificar preços
            print("O que deseja modificar?")
            print("1. Preços de sabores")
            print("2. Preços de adicionais")

            escolha = input("Escolha uma opção: ")

            if escolha == "1":  # Modificar preços de sabores
                print("\n--- Sabores disponíveis ---")
                for i, sabor in enumerate(self.cardapio["sabores"].keys(), 1):
                    print(f"{i}. {sabor}")

                opcao_sabor = int(input("Escolha o número do sabor: ")) - 1
                sabores = list(self.cardapio["sabores"].keys())

                if opcao_sabor < 0 or opcao_sabor >= len(sabores):
                    print("⚠️ Opção inválida!")
                    return

                sabor = sabores[opcao_sabor]
                print(f"\nAtualizando preços para {sabor}")

                for tamanho in self.cardapio["tamanhos"]:
                    preco_atual = self.cardapio["sabores"][sabor]["preco"][tamanho]
                    try:
                        novo_preco = float(input(f"Novo preço para {tamanho} (atual: R$ {preco_atual:.2f}): R$ "))
                        self.cardapio["sabores"][sabor]["preco"][tamanho] = novo_preco
                    except ValueError:
                        print(f"⚠️ Preço inválido para {tamanho}! Mantendo o valor atual.")

                self.salvar_dados()
                print(f"✅ Preços de {sabor} atualizados!")

            elif escolha == "2":  # Modificar preços de adicionais
                print("\n--- Adicionais disponíveis ---")
                for i, (adicional, preco) in enumerate(self.cardapio["adicionais"].items(), 1):
                    print(f"{i}. {adicional} - R$ {preco:.2f}")

                opcao_adicional = int(input("Escolha o número do adicional: ")) - 1
                adicionais = list(self.cardapio["adicionais"].keys())

                if opcao_adicional < 0 or opcao_adicional >= len(adicionais):
                    print("⚠️ Opção inválida!")
                    return

                adicional = adicionais[opcao_adicional]
                preco_atual = self.cardapio["adicionais"][adicional]

                try:
                    novo_preco = float(input(f"Novo preço para {adicional} (atual: R$ {preco_atual:.2f}): R$ "))
                    self.cardapio["adicionais"][adicional] = novo_preco
                    self.salvar_dados()
                    print(f"✅ Preço de {adicional} atualizado!")
                except ValueError:
                    print("⚠️ Preço inválido! Use apenas números.")

            else:
                print("⚠️ Opção inválida!")

        elif opcao == "5":  # Remover item
            print("O que deseja remover?")
            print("1. Sabor de pizza")
            print("2. Adicional")

            escolha = input("Escolha uma opção: ")

            if escolha == "1":  # Remover sabor
                print("\n--- Sabores disponíveis ---")
                for i, sabor in enumerate(self.cardapio["sabores"].keys(), 1):
                    print(f"{i}. {sabor}")

                opcao_sabor = int(input("Escolha o número do sabor a remover: ")) - 1
                sabores = list(self.cardapio["sabores"].keys())

                if opcao_sabor < 0 or opcao_sabor >= len(sabores):
                    print("⚠️ Opção inválida!")
                    return

                sabor = sabores[opcao_sabor]
                confirma = input(f"Confirma a remoção de '{sabor}'? (S/N): ").strip().upper()

                if confirma == "S":
                    del self.cardapio["sabores"][sabor]
                    self.salvar_dados()
                    print(f"✅ Sabor {sabor} removido do cardápio!")

            elif escolha == "2":  # Remover adicional
                print("\n--- Adicionais disponíveis ---")
                for i, adicional in enumerate(self.cardapio["adicionais"]):
                  print("\n--- Adicionais disponíveis ---")
                for i, adicional in enumerate(self.cardapio["adicionais"].keys(), 1):
                  print(f"{i}. {adicional} - R$ {self.cardapio['adicionais'][adicional]:.2f}")

                opcao_adicional = int(input("Escolha o número do adicional a remover: ")) - 1
                adicionais = list(self.cardapio["adicionais"].keys())

                if opcao_adicional < 0 or opcao_adicional >= len(adicionais):
                    print("⚠️ Opção inválida!")
                    return

                adicional = adicionais[opcao_adicional]
                confirma = input(f"Confirma a remoção de '{adicional}'? (S/N): ").strip().upper()

                if confirma == "S":
                    del self.cardapio["adicionais"][adicional]
                    self.salvar_dados()
                    print(f"✅ Adicional {adicional} removido do cardápio!")

            else:
                print("⚠️ Opção inválida!")

        elif opcao == "6":  # Voltar
            return

        else:
            print("⚠️ Opção inválida!")

    def _mostrar_cardapio(self) -> None:
        """Mostra o cardápio completo"""
        print("\n===== CARDÁPIO COMPLETO =====")

        # Mostra sabores
        print("\n🍕 SABORES DE PIZZA")
        print("=" * 50)
        for sabor, info in self.cardapio["sabores"].items():
            print(f"\n▶ {sabor}")
            print(f"  Ingredientes: {', '.join(info['ingredientes'])}")
            print("  Preços:")
            for tamanho, preco in info["preco"].items():
                print(f"   - {tamanho}: R$ {preco:.2f}")

        # Mostra adicionais
        print("\n➕ ADICIONAIS")
        print("=" * 50)
        for adicional, preco in self.cardapio["adicionais"].items():
            print(f"▶ {adicional}: R$ {preco:.2f}")

    def relatorio_vendas(self) -> None:
        """Gera um relatório de vendas"""
        if not self.historico_pedidos:
            print("📊 Nenhum pedido no histórico para gerar relatório!")
            return

        print("\n===== RELATÓRIO DE VENDAS =====")

        # Define período do relatório
        print("\nSelecione o período do relatório:")
        print("1. Último dia")
        print("2. Última semana")
        print("3. Último mês")
        print("4. Período específico")
        print("5. Todo o histórico")

        opcao = input("Escolha uma opção: ")

        hoje = datetime.datetime.now()

        if opcao == "1":  # Último dia
            data_inicio = hoje - datetime.timedelta(days=1)
            periodo = "do último dia"
        elif opcao == "2":  # Última semana
            data_inicio = hoje - datetime.timedelta(days=7)
            periodo = "da última semana"
        elif opcao == "3":  # Último mês
            data_inicio = hoje - datetime.timedelta(days=30)
            periodo = "do último mês"
        elif opcao == "4":  # Período específico
            try:
                dia_inicio = int(input("Dia inicial: "))
                mes_inicio = int(input("Mês inicial: "))
                ano_inicio = int(input("Ano inicial: "))

                dia_fim = int(input("Dia final: "))
                mes_fim = int(input("Mês final: "))
                ano_fim = int(input("Ano final: "))

                data_inicio = datetime.datetime(ano_inicio, mes_inicio, dia_inicio)
                data_fim = datetime.datetime(ano_fim, mes_fim, dia_fim, 23, 59, 59)

                periodo = f"de {dia_inicio}/{mes_inicio}/{ano_inicio} até {dia_fim}/{mes_fim}/{ano_fim}"
            except ValueError:
                print("⚠️ Dados inválidos! Usando todo o histórico.")
                data_inicio = datetime.datetime(1900, 1, 1)
                periodo = "de todo o histórico"
        else:  # Todo o histórico
            data_inicio = datetime.datetime(1900, 1, 1)
            periodo = "de todo o histórico"

        data_fim = hoje if opcao != "4" else data_fim

        # Filtra os pedidos pelo período
        pedidos_periodo = [p for p in self.historico_pedidos
                         if data_inicio <= p.data_hora <= data_fim]

        if not pedidos_periodo:
            print(f"Nenhum pedido encontrado para o período {periodo}!")
            return

        # Estatísticas básicas
        total_pedidos = len(pedidos_periodo)
        faturamento = 0

        # Contadores para análise
        sabores_populares = {}
        adicionais_populares = {}
        tamanhos_populares = {}
        vendas_por_dia = {}

        for pedido in pedidos_periodo:
            # Calcula faturamento
            if pedido.sabor in self.cardapio["sabores"] and pedido.tamanho in self.cardapio["sabores"][pedido.sabor]["preco"]:
                valor_base = self.cardapio["sabores"][pedido.sabor]["preco"][pedido.tamanho]
                valor_adicionais = sum(self.cardapio["adicionais"].get(a, 0) for a in pedido.adicional)
                valor_pedido = valor_base + valor_adicionais
                faturamento += valor_pedido

            # Contabiliza estatísticas
            # Sabores
            if pedido.sabor in sabores_populares:
                sabores_populares[pedido.sabor] += 1
            else:
                sabores_populares[pedido.sabor] = 1

            # Tamanhos
            if pedido.tamanho in tamanhos_populares:
                tamanhos_populares[pedido.tamanho] += 1
            else:
                tamanhos_populares[pedido.tamanho] = 1

            # Adicionais
            for adicional in pedido.adicional:
                if adicional in adicionais_populares:
                    adicionais_populares[adicional] += 1
                else:
                    adicionais_populares[adicional] = 1

            # Vendas por dia
            dia = pedido.data_hora.strftime("%d/%m/%Y")
            if dia in vendas_por_dia:
                vendas_por_dia[dia] += 1
            else:
                vendas_por_dia[dia] = 1

        # Exibe o relatório
        print(f"\n📊 Relatório de vendas {periodo}")
        print(f"Total de pedidos: {total_pedidos}")
        print(f"Faturamento total: R$ {faturamento:.2f}")

        # Top 3 sabores mais vendidos
        print("\nTop 3 sabores mais vendidos:")
        for i, (sabor, qtd) in enumerate(sorted(sabores_populares.items(),
                                              key=lambda x: x[1], reverse=True)[:3], 1):
            print(f"{i}. {sabor}: {qtd} pedidos")

        # Top 3 adicionais mais pedidos
        if adicionais_populares:
            print("\nTop 3 adicionais mais pedidos:")
            for i, (adicional, qtd) in enumerate(sorted(adicionais_populares.items(),
                                                      key=lambda x: x[1], reverse=True)[:3], 1):
                print(f"{i}. {adicional}: {qtd} pedidos")
        else:
            print("\nNenhum adicional foi pedido no período.")

        # Tamanhos mais pedidos
        print("\nTamanhos mais pedidos:")
        for tamanho, qtd in sorted(tamanhos_populares.items(),
                                 key=lambda x: x[1], reverse=True):
            porcentagem = (qtd / total_pedidos) * 100
            print(f"{tamanho}: {qtd} pedidos ({porcentagem:.1f}%)")

        # Vendas por dia
        print("\nVendas por dia:")
        for dia, qtd in sorted(vendas_por_dia.items()):
            print(f"{dia}: {qtd} pedidos")

def menu_principal():
    sistema = SistemaPizzaria()

    while True:
        print("\n🍕 === SISTEMA DE GESTÃO DE PIZZARIA === 🍕")
        print("1. Adicionar Pedido")
        print("2. Visualizar Fila de Pedidos")
        print("3. Entregar Pedido")
        print("4. Alterar Pedido")
        print("5. Consultar Pedido")
        print("6. Gerenciar Cardápio")
        print("7. Relatório de Vendas")
        print("8. Sair")

        opcao = input("\nEscolha uma opção: ")

        if opcao == "1":
            sistema.adicionar_pedido()
        elif opcao == "2":
            sistema.visualizar_fila()
        elif opcao == "3":
            sistema.entregar_pedido()
        elif opcao == "4":
            sistema.alterar_pedido()
        elif opcao == "5":
            sistema.consultar_pedido()
        elif opcao == "6":
            sistema.gerenciar_cardapio()
        elif opcao == "7":
            sistema.relatorio_vendas()
        elif opcao == "8":
            print("🍕 Obrigado por usar o Sistema de Gestão de Pizzaria! 👋")
            sistema.salvar_dados()
            break
        else:
            print("⚠️ Opção inválida! Tente novamente.")

if __name__ == "__main__":
    menu_principal()


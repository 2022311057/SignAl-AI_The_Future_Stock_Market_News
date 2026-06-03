# 軽量で安定しているNode.jsのベースイメージを使用します
FROM node:20-slim

# セキュリティを高めるため、root以外の専用ユーザーを作成します
RUN useradd -m -u 1001 claude

# Claude CodeのCLIをインストールします
RUN npm install -g @anthropic-ai/claude-code

# 作業ディレクトリを設定します
WORKDIR /workspace

# 作成した専用ユーザーに切り替えます
USER claude

# コンテナ起動時に自動でClaude Codeが立ち上がるようにします
ENTRYPOINT ["claude"]
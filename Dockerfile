ARG TEXLIVE_YEAR=2025
ARG TEXLIVE_MIRROR=http://mirror.ctan.org/systems/texlive/tlnet

# Stage 1: TeX Live 2025 (slim, scheme-small + required collections)
FROM debian:bookworm-slim AS texlive
ARG TEXLIVE_YEAR
ARG TEXLIVE_MIRROR

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates perl wget xz-utils fontconfig \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/install-tl && cd /tmp/install-tl \
 && wget -O install-tl.tar.gz "${TEXLIVE_MIRROR}/install-tl-unx.tar.gz" \
 && tar -xzf install-tl.tar.gz --strip-components=1 \
 && printf '%s\n' \
    'selected_scheme scheme-small' \
    'TEXDIR /usr/local/texlive/2025' \
    'TEXMFCONFIG ~/.texlive2025/texmf-config' \
    'TEXMFHOME ~/texmf' \
    'TEXMFLOCAL /usr/local/texlive/texmf-local' \
    'TEXMFSYSCONFIG /usr/local/texlive/2025/texmf-config' \
    'TEXMFSYSVAR /usr/local/texlive/2025/texmf-var' \
    'TEXMFVAR ~/.texlive2025/texmf-var' \
    'binary_x86_64-linux 1' \
    'portable 0' \
    'tlpdbopt_install_docfiles 0' \
    'tlpdbopt_install_srcfiles 0' \
    >/tmp/texlive.profile \
 && ./install-tl -profile /tmp/texlive.profile

ENV PATH=/usr/local/texlive/${TEXLIVE_YEAR}/bin/x86_64-linux:$PATH

RUN tlmgr install \
    collection-latexrecommended \
    collection-latexextra \
    collection-langenglish \
    collection-langgerman \
    collection-fontsrecommended \
    lastpage hyphenat \
 && tlmgr path add

# Stage 2: Python runtime with prebuilt TeX Live
FROM python:3.11-slim AS runtime
ARG TEXLIVE_YEAR
ENV PATH=/usr/local/texlive/${TEXLIVE_YEAR}/bin/x86_64-linux:$PATH

RUN apt-get update \
 && apt-get install -y --no-install-recommends fontconfig ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY --from=texlive /usr/local/texlive /usr/local/texlive
COPY --from=texlive /usr/local/bin/ /usr/local/bin/

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000

EXPOSE 8000

CMD ["uvicorn", "bridge.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

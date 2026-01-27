" === 基本設定 ===
set number
set cursorline
set ruler
set laststatus=2
set scrolloff=3
set title

" === 検索設定 ===
set hlsearch
set ignorecase
set smartcase
set wrapscan
" 検索後のハイライトを消すショートカット（Escを2回）
nnoremap <Esc><Esc> :nohlsearch<CR>

" === インデント設定（基本） ===
set expandtab
set tabstop=4
set softtabstop=4
set shiftwidth=4

" ファイルタイプ検出とプラグイン、インデントを有効化
filetype plugin indent on

" === ファイルタイプ別のインデント ===
augroup FileTypeIndent
  autocmd!
  " Makefileはタブ必須
  autocmd FileType make setlocal noexpandtab tabstop=4 shiftwidth=4
  
  " Web系は2スペース
  autocmd FileType javascript,typescript,json,yaml,html,css setlocal tabstop=2 shiftwidth=2 softtabstop=2
  
  " シェルスクリプトは4スペース
  autocmd FileType sh,bash,zsh setlocal tabstop=4 shiftwidth=4 softtabstop=4
  
  " Goはタブ
  autocmd FileType go setlocal noexpandtab tabstop=4 shiftwidth=4
  
  " Pythonは4スペース
  autocmd FileType python setlocal tabstop=4 shiftwidth=4 softtabstop=4
augroup END

" === 自動コメント無効化 ===
augroup auto_comment_off
  autocmd!
  autocmd FileType * setlocal formatoptions-=ro
augroup END

" === キーバインド ===
" 表示行単位で移動
nnoremap j gj
nnoremap k gk
nnoremap <Down> gj
nnoremap <Up> gk
" 逆の動作も定義
nnoremap gj j
nnoremap gk k

" 削除でyankしない（意図的なヤンクのみレジスタに入れる）
nnoremap x "_x
nnoremap d "_d
nnoremap D "_D

" === その他 ===
set encoding=utf-8
set backspace=indent,eol,start
set visualbell
set t_vb=

" macOS クリップボード連携（macOSの場合のみ）
if has('mac') || has('macunix')
  set clipboard=unnamed
endif

" Linux/Unix でクリップボード使える場合
if has('unnamedplus')
  set clipboard=unnamedplus
endif

" === シンタックスハイライト ===
syntax on
set notermguicolors
" light にしたほうが見た目が良い
set background=light

" === 不可視文字の表示（オプション、好みで有効化） ===
set list
set listchars=tab:»-,trail:-,nbsp:%,eol:↲

" === マウスサポート（Vim 8.0以降、好みで有効化） ===
if has('mouse')
  set mouse=a
endif

" === ステータスラインのカスタマイズ（オプション） ===
" ファイル名、行番号、列番号、ファイル形式を表示
set statusline=%F%m%r%h%w\ [%{&ff}]\ [%Y]\ [%04l,%04v][%p%%]\ [LEN=%L]

" === ローカル設定の読み込み ===
" マシン固有の設定があれば読み込む
if filereadable(expand('~/.vimrc_local'))
  source ~/.vimrc_local
endif

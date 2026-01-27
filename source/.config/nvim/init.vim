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
  autocmd FileType make setlocal noexpandtab tabstop=4 shiftwidth=4
  autocmd FileType javascript,typescript,json,yaml,html,css setlocal tabstop=2 shiftwidth=2 softtabstop=2
  autocmd FileType sh,bash,zsh setlocal tabstop=2 shiftwidth=2 softtabstop=2
  autocmd FileType go setlocal noexpandtab tabstop=4 shiftwidth=4
  autocmd FileType python setlocal tabstop=4 shiftwidth=4 softtabstop=4
augroup END

" === 自動コメント無効化 ===
augroup auto_comment_off
  autocmd!
  autocmd FileType * setlocal formatoptions-=ro
augroup END

" === キーバインド ===
nnoremap j gj
nnoremap k gk
nnoremap <Down> gj
nnoremap <Up> gk
nnoremap gj j
nnoremap gk k

" 削除でyankしない
nnoremap x "_x
nnoremap d "_d
nnoremap D "_D

" === その他 ===
set encoding=utf-8
set backspace=indent,eol,start
set visualbell
set t_vb=
set clipboard=unnamed

" シンタックスハイライト
syntax on
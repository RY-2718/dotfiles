" :scriptnamesで読み込んだファイルを確認できます

" vimじゃなくてviっぽい動作をしないようにする 
set nocompatible

" 表示関連の設定
" タブをスペースに展開
set expandtab
" Makefileでだけタブをスペースに展開しない
let _curfile=expand("%:r")
if _curfile == 'Makefile' || 'makefile'
    set noexpandtab
endif
" タブの画面上での幅
set tabstop=4
" Tabキーを押したときに挿入されるスペース幅
set softtabstop=4
" 自動で挿入されるインデントのスペース幅
set shiftwidth=4
" C言語スタイルのインデントを自動挿入
set cindent
" 現在行をハイライト
set cursorline
" ルーラーを表示 (noruler:非表示)
set ruler
" 行番号を表示
set number
" 常にステータス行を表示 (詳細は:he laststatus)
set laststatus=2
" n行余裕があるうちにスクロールするようにする
set scrolloff=3
" タイトルを表示
set title

" 検索関連の設定
" 検索結果をハイライト表示
set hlsearch
" 検索時に大文字小文字を無視 (noignorecase:無視しない)
set ignorecase
" 大文字小文字の両方が含まれている場合は大文字小文字を区別
set smartcase
" 検索時にファイルの最後まで行ったら最初に戻る (nowrapscan:戻らない)
set wrapscan

" 動作に関わる設定
autocmd FileType * setlocal formatoptions-=ro
" 表示行単位で上下移動するように
nnoremap j gj
nnoremap k gk
nnoremap <Down> gj
nnoremap <Up>   gk
" 逆に普通の行単位で移動したい時のために逆の map も設定しておく
nnoremap gj j
nnoremap gk k
"ビープ音を鳴らさない
set vb t_vb=
" C-AやC-Xでインクリメント/デクリメントするときに10進数として扱う
set nrformats-=octal
" バックスペースでインデントや改行を削除できるようにする
set backspace=indent,eol,start
" エンコーディングをutf-8にする
set encoding=utf-8

" 拡張子ごとに幅を設定
autocmd FileType text setlocal textwidth=0
autocmd FileType rb setlocal textwidth=108

" highlightカスタマイズ設定
autocmd ColorScheme * highlight Conceal ctermbg=none

" ローカル設定を読み込む
if filereadable(expand($HOME.'/.vimrc_local'))
  source $HOME/.vimrc_local
endif

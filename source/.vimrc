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
" 自動コメントアウトを無効化
augroup auto_comment_off
    autocmd!
    autocmd BufEnter * setlocal formatoptions-=r
    autocmd BufEnter * setlocal formatoptions-=o
augroup END

" 拡張子ごとに幅を設定
autocmd FileType text setlocal textwidth=0

" highlightカスタマイズ設定
autocmd ColorScheme * highlight Conceal ctermbg=none

" ローカル設定を読み込む
if filereadable(expand($HOME.'/.vimrc_local'))
    source $HOME/.vimrc_local
endif

" neobundle ローカル設定で変数を設定すれば動くようにしたい
if exists('enable_neobundle')
    let vimproc_dll_path = $HOME . '/.vim/bundle/vimproc.vim/lib/vimproc_mac.so'

    filetype off " for NeoBundle

    if has('vim_starting')
        set runtimepath+=$HOME/.vim/neobundle.vim/
        call neobundle#begin(expand('~/.vim/bundle/'))
        NeoBundleFetch 'Shougo/neobundle.vim'
        " ここから NeoBundle でプラグインを設定します
        "  
        " NeoBundle で管理するプラグインを追加します。
        NeoBundle 'Shougo/neocomplcache.git'
        NeoBundle 'Shougo/unite.vim.git'
        NeoBundle 'altercation/vim-colors-solarized'
        NeoBundle 'w0ng/vim-hybrid'
        NeoBundle 'Shougo/vimproc.vim', {
                    \ 'build' : {
                    \     'windows' : 'tools\\update-dll-mingw',
                    \     'cygwin' : 'make -f make_cygwin.mak',
                    \     'mac' : 'make',
                    \     'linux' : 'make',
                    \     'unix' : 'gmake',
                    \    },
                    \ }
        NeoBundle 'mattn/emmet-vim'
        NeoBundle 'pangloss/vim-javascript'
        NeoBundle 'nathanaelkane/vim-indent-guides'
        NeoBundle 'jelera/vim-javascript-syntax'
        NeoBundle 'aereal/vim-colors-japanesque'
        NeoBundle 'Vimjas/vim-python-pep8-indent'
        NeoBundle 'slim-template/vim-slim'
        NeoBundle 'posva/vim-vue'
        NeoBundle 'Shougo/context_filetype.vim'
        NeoBundle 'osyo-manga/vim-precious'
        call neobundle#end()
    endif
    filetype plugin indent on       " restore filetype
    NeoBundleCheck

    let g:neobundle#log_filename = $HOME . "/neobundle.log"

    " colorscheme
    let g:hybrid_use_iTerm_colors = 1
    set background=dark
    colorscheme japanesque
    syntax enable
endif

if has('mac')
    set ambiwidth=double
    if exists('$LANG') && $LANG ==# 'ja_JP.UTF-8'
        set langmenu=ja_ja.utf-8.macvim
    endif

    " Macではデフォルトの'iskeyword'がcp932に対応しきれていないので修正
    set iskeyword=@,48-57,_,128-167,224-235
    set clipboard+=unnamed
endif

" history
if exists('enable_history')
    set undodir=./.vimundo,$HOME/.vim_history/undo
    set undofile
    set backupdir=./.vimtmp,$HOME/.vim_history/tmp
endif

" slim
autocmd BufRead,BufNewFile *.slim setfiletype slim

" vue
autocmd BufNewFile,BufRead *.vue set filetype=html

" 削除キーでyankしない
nnoremap x "_x
nnoremap d "_d
nnoremap D "_D

if has('mac')
    let vimproc_dll_path = $HOME . '/.vim/bundle/vimproc.vim/lib/vimproc_mac.so'
endif

set nocompatible
filetype off            " for NeoBundle

if has('vim_starting')
    set rtp+=$HOME/.vim/neobundle.vim/
endif
call neobundle#begin(expand('~/.vim/bundle'))
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
call neobundle#end()
filetype plugin indent on       " restore filetype

" fundamental
set expandtab
set tabstop=4
set shiftwidth=4
set softtabstop=4
set cindent
set ruler
set number
set hlsearch
set cursorline
autocmd FileType * setlocal formatoptions-=ro
set vb t_vb=
" 表示行単位で上下移動するように
nnoremap j gj
nnoremap k gk
nnoremap <Down> gj
nnoremap <Up>   gk
" 逆に普通の行単位で移動したい時のために逆の map も設定しておく
nnoremap gj j
nnoremap gk k

" colorscheme
let g:hybrid_use_iTerm_colors = 1
set background=dark
colorscheme hybrid
syntax enable

" history
:set undodir=$HOME/.vim_history/undo
:set backupdir=$HOME/.vim_history/tmp

autocmd FileType text setlocal textwidth=0

# FindCatsInStreetview

## Cloud9 設定

### Python Setting

#### Preference

Preferences > PROJECT SETTINGS > Python Support > Python3

#### Change alias

```
$ vi ~/.bashrc
alias python=python36

$ source ~/.bashrc

$ sudo update-alternatives --config python
selection number: 2
```

### AWS Setting

```
$ vi ~/.bashrc
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXX
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXX
export AWS_DEFAULT_REGION=ap-northeast-1

$ source ~/.bashrc
```

### git Setting

```
$ git config --global user.name "xxx"
$ git config --global user.email xxx
$ git config --global core.editor vim
```
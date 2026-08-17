


 























<!DOCTYPE html>
<html>

<head>
    <!--  <script type="text/javascript">	
	var _uxt = _uxt || [];
</script>  -->
    <meta charset="UTF-8">
    <title>服务与隐私协议</title>
    <meta name="viewport" content="user-scalable=no, initial-scale=1, maximum-scale=1, minimum-scale=1, width=device-width, height=device-height" />
    <meta name="apple-touch-fullscreen" content="yes" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black" />
    <meta name="format-detection" content="telephone=no" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <!--360浏览器基于Webkit内核浏览-->
    <meta name="render" content="webkit">
    <script>
        function Rem() {
            var docEl = document.documentElement;
            var oSize = docEl.clientWidth / 7.5;
            if (oSize > 85) {
                oSize = 85;
            }
            docEl.style.fontSize = oSize + 'px';
        }
        window.addEventListener('resize', Rem, false);
        Rem();
    </script>
    <!-- 图标 -->
    <link href="https://static.e.189.cn/e/2016/source/stylesheets/passport-wap/agreementANDquestion/agreement_describe.css" rel="stylesheet">
    <!-- <script>
	var _ux21et = (new Date()).getTime();	
	var isTopHeader = location.search.indexOf('topHeader=true') !== -1 || sessionStorage.getItem('topHeader') ? true: false;
	if(isTopHeader) {
		sessionStorage.setItem('topHeader', 1);
		document.documentElement.classList.add('page-header')
	}
</script> 
<style>
	.page-header .note-header {box-sizing: content-box; padding-top: 23px;}
	.page-header .note-header .title{top: auto; bottom: 0;}
</style> -->
    


<script type="text/javascript">
var isLogin = 'false'=='true'?true:false;
var closeMyPageStr = "{\"result\":-5001,\"msg\":\"关闭我的页面\"}";
var logoutStr = "{\"result\":-7001,\"msg\":\"退出登录\"}";
var closeWebviewStr = "{\"result\":-7002,\"msg\":\"退出登录，关闭webview\"}";
var notifyLoginStr = "{\"result\":-7003,\"msg\":\"其他需登录而未登录点击\"}";
var accountInfoModifyStr = "{\"result\":7004,\"msg\":\"用户已经进行了用户信息修改，建议进行用户信息查询进行更新\"}";
var passwordModifyStr = "{\"result\":7005,\"msg\":\"用户更改了密码，原accessToken已失效，需重新登录获取\"}";
var loginStr = "{\"result\":7000,\"msg\":\"登录成功\",\"accessToken\":\"\"}";
function close(){
	getJsBrigeSdkFunc("myPageColse", closeMyPageStr);
}
function logout(){
	getJsBrigeSdkFunc("loginOut", logoutStr);
}

function back_v2(url){
	try {
		if(url == null || url == '' || url == '/wap/login.do'
				|| url == '/wap/centre.do' || url == 'http://e.189.cn/wap/centre.do'){
			getJsBrigeSdkFunc("methodWithJsonPara", closeWebviewStr);
		}
		location.href = url;
	} catch (e) {
		location.href = url;
	}
}

function back(url){
	try {
	    getJsBrigeSdkFunc("methodWithJsonPara", closeWebviewStr);
		location.href = url;
	} catch (e) {
		location.href = url;
	}
}
function login(){
	try {
		getJsBrigeSdkFunc("methodWithJsonPara", notifyLoginStr);
	} catch (e) {
		//location.href = "http://e.189.cn/wap/index.do?returnUrl=https%3A%2F%2Fe.189.cn%2Fsdk%2Fwap%2Findex.do";
	}
}
function checkLoginRedirect(url){
	if(!isLogin){
		login();
	} else {
		location.href = url;
	}
}
function checkLogin(){
	if(!isLogin){
		login();
	}
}
function accountInfoModify(){
	try {
		getJsBrigeSdkFunc("methodWithJsonPara", accountInfoModifyStr);
	} catch (e) {
	}
}
function passwordModify(){
	try {
        getJsBrigeSdkFunc("methodWithJsonPara", passwordModifyStr);
	} catch (e) {
	}
}
function loginRedircet(url){
    if(getJsBrigeSdkFunc("logined", loginStr) === false) {
        location.href = url;
	}
}

function getJsBrigeSdkFunc(fName, params) {
    if (window.JSKitOnClient && typeof window.JSKitOnClient[fName] === 'function') {
        if (params && params.length > 0) {
            return window.JSKitOnClient[fName](params)
        } else {
            return window.JSKitOnClient[fName]()
        }
    } else {
        try{
            window.webkit.messageHandlers.iOSSDKTest.postMessage(null);
        } catch (e) {
            return false;
        }
        var m = window.prompt(fName, params);
        if (m !== "MethodNotFound") {
            return m;
        }
        return false;
    }
}

/*校验客户端是否存在方法 异步*/
async function getAsyncJsBrigeSdkFunc(fName, params) {
	if (window.JSKitOnClient && typeof window.JSKitOnClient[fName] === 'function') {
		var callback;
		if (params && params.length > 0) {
			callback = await window.JSKitOnClient[fName](params)
		} else {
			callback = await window.JSKitOnClient[fName]()
		}
		return callback
	} else {
		try {
			window.webkit.messageHandlers.iOSSDKTest.postMessage(null)
		} catch (e) {
			return false
		}
		var m = window.prompt(fName, params)
		if (m !== 'MethodNotFound') {
			return m
		}
		return false
	}
}

function isHarmonyOS() {
	// 检查userAgent中是否包含HarmonyOS关键词
	var ua = navigator.userAgent;
	var keywords = ['HarmonyOS','OpenHarmony','Harmony', 'harmony']
	return keywords.some(function (keywords) {
		return ua.includes(keywords);
	});
}

function redirect(url) {
	var toPageStr = "{\"toUrl\":\""+decodeURI(url)+"\"}";
			setTimeout (function(){
			    var result = getJsBrigeSdkFunc("redirectJs", toPageStr);
                if(result === false) {
                    back_v2(url);
                }
			}, 0);
	}
</script>
    

</head>

<body ontouchstart="">

    
            <header class="note-header note-header-fixed">
                <a href="javascript:redirect('https%3A%2F%2Fe.189.cn%2Fsdk%2Fagreement%2Fdetail.do%3FappKey%3D%26returnUrl%3Dhttps%253A%252F%252Fe.dlife.cn');" class="ui-button-back"></a>
                <p class="title">服务与隐私协议</p>
            </header>
            <ul class="faq-lists faq-lists-fixed" id="j-help-lists">
        

    
        <li class="faq-lists-li" data-item=1>天翼账号服务协议<i class="icons-next right"></i></li>
    
        <li class="faq-lists-li" data-item=1>天翼账号隐私政策<i class="icons-next right"></i></li>
    

    </ul>
    <div style="width: 100%; height: 100%;">
        
            <div class="agreement-info hide" style="height: 100%;padding-bottom:50px;">
                <iframe id="loginIframe" frameborder="0" style="border: 0; padding: 0; margin: 0; width: 100%; height: 100%" src="https://id.189.cn/html/agreement_538.html">
                </iframe>
            </div>
        
            <div class="agreement-info hide" style="height: 100%;padding-bottom:50px;">
                <iframe id="loginIframe" frameborder="0" style="border: 0; padding: 0; margin: 0; width: 100%; height: 100%" src="https://id.189.cn/html/agreement_709.html">
                </iframe>
            </div>
        
    </div>

    <script>
        var iconsNext = document.getElementsByClassName('icons-next');
        var list = document.getElementsByClassName('faq-lists-li');
        var listHeight = list[0].clientHeight;
        var listAccount = list.length;
        var agreementInfo = document.getElementsByClassName('agreement-info');
        handleList(0)

        function handleList(index) {
            /*处理箭头转向 */
            for (var i = 0; i < iconsNext.length; i++) {
                if (index !== i) {
                    iconsNext[i].className = "icons-next right";
                }
            }
            if (iconsNext[index].className.indexOf("right") != -1) {
                iconsNext[index].className = "icons-next bottom";
            } else {
                iconsNext[index].className = "icons-next right";
            }

            /* 处理协议内容的展示与隐藏 */
            for (var j = 0; j < agreementInfo.length; j++) {
                if (index !== j) {
                    agreementInfo[j].className = "agreement-info hide";
                }
            }
            if (agreementInfo[index].className.indexOf("hide") != -1) {
                agreementInfo[index].className = "agreement-info block";
            } else {
                agreementInfo[index].className = "agreement-info hide";
            }

            /* 处理列表标题位置 */
            var _fixListLength = list.length - index;
            if (iconsNext[index].className.indexOf("right") != -1) {
                for (var k = 0; k < iconsNext.length; k++) {
                    list[k].className = "faq-lists-li";
                    list[k].style.bottom = 'auto';
                }
            } else {
                if (index !== listAccount - 1) {
                    for (var k = 0; k < iconsNext.length; k++) {
                        list[k].className = "faq-lists-li";
                        list[k].style.bottom = 'auto';
                    }
                    for (var z = 1; z < _fixListLength; z++) {
                        list[index + z].className = "faq-lists-li list-fixed";
                        list[index + z].style.bottom = listHeight * (_fixListLength - z - 1) + 'px';
                    }
                } else {
                    for (var l = 0; l < iconsNext.length; l++) {
                        list[l].className = "faq-lists-li";
                        list[l].style.bottom = 'auto';
                    }
                }
            }

            /* 处理协议内容显示不全 */
            if (document.getElementsByClassName("faq-lists-fixed")[0]) {
                var _paddingHeight = 20;
                var _marginTop = 1.9;
                for (var y = 0; y < listAccount; y++) {
                    if (list[y].className.indexOf("list-fixed") != -1) {
                        _paddingHeight = _paddingHeight + listHeight;
                    }
                }
                _marginTop = _marginTop + index;
                agreementInfo[index].style.marginTop = _marginTop + 'rem';
                agreementInfo[index].style.paddingBottom = _paddingHeight + 'px';
                window.scrollTo({
                    top: 0
                })
            }else{
                var _paddingHeight = 20;
                var _marginTop = 0;
                for (var y = 0; y < listAccount; y++) {
                    if (list[y].className.indexOf("list-fixed") != -1) {
                        _paddingHeight = _paddingHeight + listHeight;
                    }
                }
                agreementInfo[index].style.marginTop = _marginTop + 'rem';
                agreementInfo[index].style.paddingBottom = _paddingHeight + 'px';
                window.scrollTo({
                    top: 0
                })
            }
        }
    </script>
</body>

</html>
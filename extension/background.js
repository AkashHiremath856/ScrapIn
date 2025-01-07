chrome.runtime.onInstalled.addListener(() => {
    console.log("Extension installed.");
});

chrome.action.onClicked.addListener(() => {
    chrome.tabs.create({ url: chrome.runtime.getURL('login.html') });
});

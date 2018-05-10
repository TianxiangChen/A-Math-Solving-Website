// Get the modal
var modal = document.getElementById('myModal');

// Get the image and insert it inside the modal - use its "alt" text as a caption
var imgs = document.getElementsByClassName('img-responsive');
var modalImg = document.getElementById("modalImg");
var captionText = document.getElementById("caption");

console.log("Running this file")

for (var i = 0; i < imgs.length; i++) {
    console.log(imgs[i].src)
    var img = imgs[i]
    img.onclick = function() {
        modal.style.display = "block";
        modalImg.src = this.src;
        captionText.innerHTML = "Fuck this shitttt";
        modalImg2.src = this.src;
        modalImg3.src = this.src;
        modalImg4.src = this.src;
    }
}

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}
